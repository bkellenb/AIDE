'''
    2020 Benjamin Kellenberger
'''

from psycopg2 import sql
from tqdm import tqdm
import torch
from detectron2.data import build_detection_test_loader

from ai.models.detectron2.genericDetectronModel import GenericDetectron2Model
from ai.models.detectron2._functional.util import intersectionOverUnion
from ai.models.detectron2._functional.datasetMapper import Detectron2DatasetMapper
from ai.models.detectron2._functional.dataset import getDetectron2Data



class GenericDetectron2BoundingBoxModel(GenericDetectron2Model):


    def calculateClassCorrelations(self, model, modelClasses, targetClasses, updateStateFun, maxNumImagesPerClass=None):
        '''
            Implementation for bounding box models.
            Here, the correlation c between a predicted p and target t box
            is defined as:
                c(p,t) = IOU(p,t) * conf(p)

        '''
        #TODO: safety checks; update state fun; etc.
        

        # query data
        queryArgs = [tuple((l,) for l in targetClasses)]
        if isinstance(maxNumImagesPerClass, int):
            limitStr = sql.SQL('LIMIT %s')      #TODO: overall limit, not per class...
            queryArgs.append(maxNumImagesPerClass)
        else:
            limitStr = sql.SQL('')

        queryStr = sql.SQL('''
            SELECT image, filename, label, x, y, width, height
            FROM {id_anno} AS a
            JOIN {id_img} AS img
            ON a.image = img.id
            WHERE label IN %s
            {limitStr}
        ''').format(
            id_anno=sql.Identifier(self.project, 'annotation'),
            id_img=sql.Identifier(self.project, 'image'),
            limitStr=limitStr
        )
        result = self.dbConnector.execute(queryStr, tuple(queryArgs), 'all')
        imgDict = {}
        for r in result:
            imgID = r['image']
            if imgID not in imgDict:
                imgDict[imgID] = {
                    'filename': r['filename'],
                    'annotations': []
                }
            imgDict[imgID]['annotations'].append(r)
        data = {
            'labelClasses': targetClasses,
            'images': imgDict
        }

        # prepare result vector
        correlations = torch.zeros(len(targetClasses), len(modelClasses))
        counts = correlations.clone()

        # prepare data loader
        transforms = self.initializeTransforms(mode='inference')

        datasetMapper = Detectron2DatasetMapper(self.project, self.fileServer, transforms, False)
        dataLoader = build_detection_test_loader(
            dataset=getDetectron2Data(data, False, False),
            mapper=datasetMapper,
            num_workers=0
        )
        dataLoaderIter = iter(dataLoader)
        numImgs = len(imgDict)

        # perform forward pass over all images
        updateStateFun(state='PROGRESS', message='predicting images with new label classes')
        model.eval()
        with torch.no_grad():
            for idx in tqdm(range(numImgs)):
                try:
                    batch = next(dataLoaderIter)
                except:
                    break

                outputs = model(batch)
                outputs = outputs[0]['instances']

                # calc. correlation per target instance and label class
                targets = batch[0]['instances']
                gtLabels = targets.get('gt_classes')

                ious = intersectionOverUnion(outputs.get('pred_boxes').tensor, targets.get('gt_boxes').tensor)
                confidences = outputs.get('scores')
                predLabels = outputs.get('pred_classes')

                valid = torch.nonzero(ious, as_tuple=False)
                corr = ious[valid[:,0], valid[:,1]] * confidences[valid[:,0]]
                correlations[gtLabels[valid[:,1]], predLabels[valid[:,0]]] += corr.cpu()
                counts[gtLabels[valid[:,1]], predLabels[valid[:,0]]] += 1

                updateStateFun(state='PROGRESS', message='predicting', done=(idx+1), total=numImgs)

            # average correlations
            valid = (counts > 0)
            correlations[valid] /= counts[valid]

            # normalize
            correlations /= correlations.sum(1).unsqueeze(1)
            
            return correlations