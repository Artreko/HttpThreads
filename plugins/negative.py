import cv2


class Plugin:
    # Имя плагина
    NAME = 'NegativeEdit'
    # Автор
    AUTHOR = 'Artik'
    # Версия
    VERSION = '0.1'
    # Краткое описание
    CAPTION = 'Негатив'

    @staticmethod
    def edit_img(img):
        for i in range(img.shape[1]):
            for j in range(img.shape[0]):
                img.itemset((j, i, 0), 255 - img.item(j, i, 0))
                img.itemset((j, i, 1), 255 - img.item(j, i, 1))
                img.itemset((j, i, 2), 255 - img.item(j, i, 2))


if __name__ == '__main__':
    img = cv2.imread('..\\noimg.jpg')
    cv2.imshow('',img)
    print(img.shape)
    Plugin.edit_img(img)
    cv2.imshow('',img)
    cv2.waitKey(0)