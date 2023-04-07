import cv2


class Plugin:
    # Имя плагина
    NAME = 'BlackWhiteEdit'
    # Автор
    AUTHOR = 'Artik'
    # Версия
    VERSION = '0.1'
    # Краткое описание
    CAPTION = 'ЧБ'

    @staticmethod
    def edit_img(img):
        for i in range(img.shape[1]):
            for j in range(img.shape[0]):
                avg = img.item(j, i, 0) + img.item(j, i, 1) + img.item(j, i, 2)
                avg /= 3
                img.itemset((j, i, 0), avg)
                img.itemset((j, i, 1), avg)
                img.itemset((j, i, 2), avg)


if __name__ == '__main__':
    img = cv2.imread('20.jpg')
    cv2.imshow('',img)
    print(img.shape)
    Plugin.edit_img(img)
    cv2.imshow('',img)
    cv2.waitKey(0)