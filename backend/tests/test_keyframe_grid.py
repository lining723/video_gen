"""关键帧数据模型单元测试"""
import unittest
from backend.src.schemas.keyframe_grid import KeyframeGrid, KeyframeFrame


class TestKeyframeGrid(unittest.TestCase):
    """测试关键帧数据模型"""

    def test_keyframe_frame_creation(self):
        """测试KeyframeFrame创建"""
        frame = KeyframeFrame(
            position=0,
            time_ratio=0.0,
            image_path="/path/to/image.png",
            status="succeeded",
        )
        self.assertEqual(frame.position, 0)
        self.assertEqual(frame.time_ratio, 0.0)
        self.assertEqual(frame.image_path, "/path/to/image.png")
        self.assertEqual(frame.status, "succeeded")

    def test_keyframe_frame_defaults(self):
        """测试KeyframeFrame默认值"""
        frame = KeyframeFrame(position=1, time_ratio=0.5)
        self.assertEqual(frame.image_path, "")
        self.assertEqual(frame.source_url, "")
        self.assertEqual(frame.status, "pending")
        self.assertEqual(frame.error_message, "")
        self.assertEqual(frame.retry_count, 0)

    def test_keyframe_grid_creation(self):
        """测试KeyframeGrid创建"""
        frames = [
            KeyframeFrame(position=i, time_ratio=i / 8.0)
            for i in range(9)
        ]
        grid = KeyframeGrid(
            project_id="proj_001",
            shot_id="shot_001",
            subject_name="主角",
            grid_type="3x3",
            frame_count=9,
            frames=frames,
            generated_at="2024-01-01T00:00:00Z",
        )
        self.assertEqual(grid.project_id, "proj_001")
        self.assertEqual(grid.shot_id, "shot_001")
        self.assertEqual(grid.grid_type, "3x3")
        self.assertEqual(grid.frame_count, 9)
        self.assertEqual(len(grid.frames), 9)

    def test_keyframe_grid_validate_success(self):
        """测试验证通过的情况"""
        frames = [
            KeyframeFrame(position=i, time_ratio=i / 15.0)
            for i in range(16)
        ]
        grid = KeyframeGrid(
            project_id="proj_001",
            shot_id="shot_001",
            subject_name="主角",
            grid_type="4x4",
            frame_count=16,
            frames=frames,
            generated_at="2024-01-01T00:00:00Z",
        )
        # 不应抛出异常
        grid.validate()

    def test_keyframe_grid_validate_invalid_type(self):
        """测试无效的网格类型"""
        frames = [KeyframeFrame(position=0, time_ratio=0.0)]
        grid = KeyframeGrid(
            project_id="proj_001",
            shot_id="shot_001",
            subject_name="主角",
            grid_type="5x5",  # 无效类型
            frame_count=1,
            frames=frames,
            generated_at="2024-01-01T00:00:00Z",
        )
        with self.assertRaises(ValueError):
            grid.validate()

    def test_keyframe_grid_validate_mismatch(self):
        """测试帧数量与网格类型不匹配"""
        frames = [
            KeyframeFrame(position=i, time_ratio=i / 8.0)
            for i in range(9)
        ]
        grid = KeyframeGrid(
            project_id="proj_001",
            shot_id="shot_001",
            subject_name="主角",
            grid_type="2x2",  # 应该是4帧
            frame_count=9,    # 但提供了9帧
            frames=frames,
            generated_at="2024-01-01T00:00:00Z",
        )
        with self.assertRaises(ValueError):
            grid.validate()

    def test_keyframe_grid_to_dict(self):
        """测试转换为字典"""
        frames = [KeyframeFrame(position=0, time_ratio=0.0)]
        grid = KeyframeGrid(
            project_id="proj_001",
            shot_id="shot_001",
            subject_name="主角",
            grid_type="2x2",
            frame_count=4,
            frames=frames,
            generated_at="2024-01-01T00:00:00Z",
        )
        data = grid.to_dict()
        self.assertIn("project_id", data)
        self.assertIn("shot_id", data)
        self.assertIn("grid_type", data)
        self.assertIn("frames", data)
        self.assertIsInstance(data["frames"], list)  # 帧列表


if __name__ == '__main__':
    unittest.main()
