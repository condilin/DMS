from openslide import AbstractSlide
from Aslide.tmap import tmap_lowlevel


class TmapSlide(AbstractSlide):
    def __init__(self, filename):
        AbstractSlide.__init__(self)
        self.__filename = filename
        self._osr = tmap_lowlevel.open_tmap_file(filename)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__filename)

    @classmethod
    def detect_format(cls, filename):
        return "un"

    @classmethod
    def get_scan_scale(self):
        return tmap_lowlevel.get_scan_scale(self._osr)

    # 关闭图像
    def close(self):
        tmap_lowlevel.close_tmap_file(self._osr)

    # 获取当前的对焦面数值
    @property
    def get_focus_layer(self):
        return tmap_lowlevel.get_focus_layer(self._osr)

    # 获取Tmap文件的总共图像块数目
    @property
    def get_tile_mumber(self):
        return tmap_lowlevel.get_tile_mumber(self._osr)

    # 获取格式文件的版本号
    @property
    def get_tmap_version(self):
        return tmap_lowlevel.get_tmap_version(self._osr)

    # 获取Tmap格式文件的整体图片信息
    @property
    def get_pixel_size(self):
        return tmap_lowlevel.get_pixel_size(self._osr)

    @property
    def dimensions(self):
        return tmap_lowlevel.get_dimensions(self._osr)

    @property
    def level_count(self):
        return tmap_lowlevel.get_level_count(self._osr)

    @property
    def level_dimensions(self):
        return tmap_lowlevel.get_level_dimensions(self._osr)

    @property
    def level_downsamples(self):
        return tmap_lowlevel.get_level_downsamples(self._osr)

    # 获取Tmap格式文件的整体图片信息
    def get_image_info_ex(self, etype):
        return tmap_lowlevel.get_image_info_ex(self._osr, etype)

    # 获取Tmap格式文件的切片数字图像信息
    def get_image_data(self, etype):
        return tmap_lowlevel.get_image_data(self._osr, etype)

    # 获取Tmap格式文件的数据
    def get_image_size_ex(self, location, size, fScale=40.0):
        nLeft = location[0]
        nTop = location[1]
        nRight = nLeft + size[0]
        nBottom = nTop + size[1]
        return tmap_lowlevel.get_image_size_ex(self._osr, nLeft, nTop, nRight, nBottom, fScale)

    @property
    def associated_images(self):
        return tmap_lowlevel.get_image_data(self._osr, 3)

    # 获取Tmap格式文件的切片数字图像
    def read_region(self, location, level, size, nIndex=0):
        nLeft = location[0]
        nTop = location[1]
        nRight = nLeft + size[0]
        nBottom = nTop + size[1]
        return tmap_lowlevel.get_crop_image_data_ex(self._osr, nIndex, nLeft, nTop, nRight, nBottom)

    def get_thumbnail(self, size=None):
        image = tmap_lowlevel.get_image_data(self._osr, 0)
        if size:
            return image.resize(size)

        return image


def main():
    slide = TmapSlide('/home/kyfq/SZH00011.TMAP')

    img = slide.read_region((20000, 6000), 0, (1216, 1216))
    img.save('./read_region.jpg')
    #
    # for i in range(5):
    #     img = slide.get_image_data(i)
    #     img.show()
    # print(slide.properties)

    # img = slide.get_thumbnail()
    # img.save('./get_thumbnail.jpg')

    print(slide.dimensions)

    slide.close()


if __name__ == '__main__':
    main()
