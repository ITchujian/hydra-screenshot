import cv2
import numpy as np


def merge_image_with_match_template(original_image: np.ndarray, target_image: np.ndarray, only_offset: bool = False):
    """
    通过模板匹配法 合并两张图像
    !!! 输入图像必须是rgb通道图像
    !!! target_image至少前10%部分必须包含在original_image中
    !!! 输出也是rbg三通道图像
    """
    # 图像灰度
    gray_a = cv2.cvtColor(original_image, cv2.COLOR_RGB2GRAY)
    gray_b = cv2.cvtColor(target_image, cv2.COLOR_RGB2GRAY)[:gray_a.shape[0], :]
    # 去除边界非目标因素的影响  头部去除5%  两边各去除10%
    gray_b_resize = gray_b[int(gray_b.shape[0] * 0.05): int(gray_b.shape[0] * 0.2),
                    int(gray_b.shape[1] * 0.1):int(gray_b.shape[1] * 0.9)]
    res = cv2.matchTemplate(gray_b_resize, gray_a, cv2.TM_SQDIFF_NORMED)
    min_val, _, min_loc, _ = cv2.minMaxLoc(res)
    if min_val < 0.01:
        if only_offset:
            return min_loc[1] - int(target_image.shape[0] * 0.05)
        stack_image = np.vstack((original_image[:min_loc[1], :], target_image[int(gray_b.shape[0] * 0.05):, :]))
        return stack_image
    else:
        raise Exception('找不到匹配目标')


def merge_images(images: list | tuple):
    if images:
        result = cv2.cvtColor(images[0], cv2.COLOR_RGB2BGR)
        for i in range(1, len(images)):
            try:
                result = merge_image_with_match_template(result, cv2.cvtColor(images[i], cv2.COLOR_RGB2BGR))
            except Exception as e:
                print(e)
        return result
    return None


def save_merge_result(path: str, result):
    # print(f"保存 -- {path}")
    cv2.imencode(f'.{path.split(".")[-1]}', result)[1].tofile(path)


def get_rgb_image(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
