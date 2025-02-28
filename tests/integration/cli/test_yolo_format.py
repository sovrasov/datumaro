import os.path as osp
from unittest import TestCase

import numpy as np

import datumaro.plugins.data_formats.voc.format as VOC
from datumaro.components.annotation import AnnotationType, Bbox
from datumaro.components.dataset import Dataset
from datumaro.components.dataset_base import DatasetItem
from datumaro.components.media import Image

from ...requirements import Requirements, mark_requirement

from tests.utils.assets import get_test_asset_path
from tests.utils.test_utils import TestDir, compare_datasets
from tests.utils.test_utils import run_datum as run


class YoloIntegrationScenarios(TestCase):
    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_save_and_load_yolo_dataset(self):
        target_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id="1",
                    subset="train",
                    media=Image.from_numpy(data=np.ones((10, 15, 3))),
                    annotations=[
                        Bbox(0.0, 2.0, 4.0, 2.0, label=2, id=0, group=0),
                        Bbox(3.0, 3.0, 2.0, 3.0, label=4, id=1, group=1),
                    ],
                )
            ],
            categories=["label_" + str(i) for i in range(10)],
        )

        with TestDir() as test_dir:
            yolo_dir = get_test_asset_path("yolo_dataset")

            run(self, "project", "create", "-o", test_dir)
            run(self, "project", "import", "-p", test_dir, "-f", "yolo", yolo_dir)

            export_dir = osp.join(test_dir, "export_dir")
            run(
                self,
                "project",
                "export",
                "-p",
                test_dir,
                "-o",
                export_dir,
                "-f",
                "yolo",
                "--",
                "--save-media",
            )

            parsed_dataset = Dataset.import_from(export_dir, format="yolo")
            compare_datasets(self, target_dataset, parsed_dataset)

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_export_mot_as_yolo(self):
        target_dataset = Dataset.from_iterable(
            [DatasetItem(id="1", subset="train", annotations=[Bbox(0.0, 4.0, 4.0, 8.0, label=2)])],
            categories=["label_" + str(i) for i in range(10)],
        )

        with TestDir() as test_dir:
            mot_dir = get_test_asset_path("mot_dataset")

            run(self, "project", "create", "-o", test_dir)
            run(self, "project", "import", "-p", test_dir, "-f", "mot_seq", mot_dir)

            yolo_dir = osp.join(test_dir, "yolo_dir")
            run(
                self,
                "project",
                "export",
                "-p",
                test_dir,
                "-o",
                yolo_dir,
                "-f",
                "yolo",
                "--",
                "--save-media",
            )

            parsed_dataset = Dataset.import_from(yolo_dir, format="yolo")
            compare_datasets(self, target_dataset, parsed_dataset)

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_convert_voc_to_yolo(self):
        target_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id="2007_000001",
                    subset="train",
                    media=Image.from_numpy(data=np.ones((10, 20, 3))),
                    annotations=[
                        Bbox(1.0, 2.0, 2.0, 2.0, label=8, id=0, group=0),
                        Bbox(5.5, 6.0, 2.0, 2.0, label=22, id=1, group=1),
                        Bbox(4.0, 5.0, 2.0, 2.0, label=15, id=2, group=2),
                    ],
                ),
                DatasetItem(
                    id="2007_000002",
                    subset="test",
                    media=Image.from_numpy(data=np.ones((10, 20, 3))),
                ),
            ],
            categories=[
                label.name
                for label in VOC.make_voc_categories(task=VOC.VocTask.voc)[AnnotationType.label]
            ],
        )

        with TestDir() as test_dir:
            voc_dir = get_test_asset_path(
                "voc_dataset",
                "voc_dataset1",
            )
            yolo_dir = osp.join(test_dir, "yolo_dir")

            run(
                self,
                "convert",
                "-if",
                "voc",
                "-i",
                voc_dir,
                "-f",
                "yolo",
                "-o",
                yolo_dir,
                "--",
                "--save-media",
            )

            parsed_dataset = Dataset.import_from(yolo_dir, format="yolo")
            compare_datasets(self, target_dataset, parsed_dataset, require_media=True)

    @mark_requirement(Requirements.DATUM_GENERAL_REQ)
    def test_can_delete_labels_from_yolo_dataset(self):
        target_dataset = Dataset.from_iterable(
            [
                DatasetItem(
                    id="1",
                    subset="train",
                    media=Image.from_numpy(data=np.ones((10, 15, 3))),
                    annotations=[Bbox(0.0, 2.0, 4.0, 2.0, label=0)],
                )
            ],
            categories=["label_2"],
        )

        with TestDir() as test_dir:
            yolo_dir = get_test_asset_path("yolo_dataset")

            run(self, "project", "create", "-o", test_dir)
            run(self, "project", "import", "-p", test_dir, "-f", "yolo", yolo_dir)

            run(
                self,
                "filter",
                "-p",
                test_dir,
                "-m",
                "i+a",
                "-e",
                "/item/annotation[label='label_2']",
            )

            run(
                self,
                "transform",
                "-p",
                test_dir,
                "-t",
                "remap_labels",
                "--",
                "-l",
                "label_2:label_2",
                "--default",
                "delete",
            )

            export_dir = osp.join(test_dir, "export")
            run(
                self,
                "project",
                "export",
                "-p",
                test_dir,
                "-o",
                export_dir,
                "-f",
                "yolo",
                "--",
                "--save-media",
            )

            parsed_dataset = Dataset.import_from(export_dir, format="yolo")
            compare_datasets(self, target_dataset, parsed_dataset)
