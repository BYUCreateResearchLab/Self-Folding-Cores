from pathlib import Path
import tempfile
import unittest

from shape_replicator import Shape, export_shapes_to_svg, replicate_shape


class ShapeReplicatorTests(unittest.TestCase):
    def test_replicate_shape_applies_spacing(self):
        shape = Shape.from_points([(0, 0), (1, 0), (0, 1)])
        replicas = replicate_shape(shape, count=3, spacing=(2, 3), start_offset=(1, 1))

        self.assertEqual(replicas[0].points, ((1, 1), (2, 1), (1, 2)))
        self.assertEqual(replicas[1].points, ((3, 4), (4, 4), (3, 5)))
        self.assertEqual(replicas[2].points, ((5, 7), (6, 7), (5, 8)))

    def test_export_shapes_to_svg_writes_polygons(self):
        shape = Shape.from_points([(0, 0), (2, 0), (1, 2)])
        replicas = replicate_shape(shape, count=2, spacing=(3, 0))

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "shapes.svg"
            export_shapes_to_svg(replicas, output)
            content = output.read_text(encoding="utf-8")

        self.assertIn("<svg", content)
        self.assertEqual(content.count("<polygon"), 2)


if __name__ == "__main__":
    unittest.main()
