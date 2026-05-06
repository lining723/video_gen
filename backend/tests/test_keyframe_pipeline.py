"""关键帧流水线单元测试"""
import unittest
from backend.src.orchestrators.keyframe_pipeline import calculate_grid_size, calculate_time_ratios


class TestKeyframePipeline(unittest.TestCase):
    """测试关键帧流水线核心函数"""

    def test_calculate_grid_size_2x2(self):
        """测试1-3秒镜头返回2x2网格"""
        # 边界值测试
        self.assertEqual(calculate_grid_size(1), ("2x2", 4))
        self.assertEqual(calculate_grid_size(2), ("2x2", 4))
        self.assertEqual(calculate_grid_size(3), ("2x2", 4))

    def test_calculate_grid_size_3x3(self):
        """测试4-6秒镜头返回3x3网格"""
        self.assertEqual(calculate_grid_size(4), ("3x3", 9))
        self.assertEqual(calculate_grid_size(5), ("3x3", 9))
        self.assertEqual(calculate_grid_size(6), ("3x3", 9))

    def test_calculate_grid_size_4x4(self):
        """测试7-10秒镜头返回4x4网格"""
        self.assertEqual(calculate_grid_size(7), ("4x4", 16))
        self.assertEqual(calculate_grid_size(8), ("4x4", 16))
        self.assertEqual(calculate_grid_size(9), ("4x4", 16))
        self.assertEqual(calculate_grid_size(10), ("4x4", 16))

    def test_calculate_grid_size_edge_cases(self):
        """测试边界情况"""
        # 0或负数使用默认值6秒
        self.assertEqual(calculate_grid_size(0), ("3x3", 9))
        self.assertEqual(calculate_grid_size(-1), ("3x3", 9))

        # 超过10秒按10处理
        self.assertEqual(calculate_grid_size(15), ("4x4", 16))
        self.assertEqual(calculate_grid_size(100), ("4x4", 16))

    def test_calculate_time_ratios_9_frames(self):
        """测试9帧时间进度分布"""
        ratios = calculate_time_ratios(9)
        self.assertEqual(len(ratios), 9)
        self.assertEqual(ratios[0], 0.0)
        self.assertEqual(ratios[-1], 1.0)
        # 验证均匀分布
        self.assertAlmostEqual(ratios[4], 0.5, places=3)

    def test_calculate_time_ratios_4_frames(self):
        """测试4帧时间进度分布"""
        ratios = calculate_time_ratios(4)
        self.assertEqual(len(ratios), 4)
        self.assertEqual(ratios[0], 0.0)
        self.assertEqual(ratios[-1], 1.0)
        self.assertAlmostEqual(ratios[1], 0.333, places=3)
        self.assertAlmostEqual(ratios[2], 0.667, places=3)

    def test_calculate_time_ratios_16_frames(self):
        """测试16帧时间进度分布"""
        ratios = calculate_time_ratios(16)
        self.assertEqual(len(ratios), 16)
        self.assertEqual(ratios[0], 0.0)
        self.assertEqual(ratios[-1], 1.0)

    def test_calculate_time_ratios_1_frame(self):
        """测试1帧特殊情况"""
        ratios = calculate_time_ratios(1)
        self.assertEqual(len(ratios), 1)
        self.assertEqual(ratios[0], 0.0)


if __name__ == '__main__':
    unittest.main()
