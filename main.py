import requests
import os
import json
from tqdm import tqdm

def token_vk(file_name):
    """Функция для чтения токена и ID пользователя из файла"""
    with open(os.path.join(os.getcwd(), file_name), 'r') as f:
        token = f.readline().strip()
        id = f.readline().strip()
    return [token, id]


def max_size_photo(photo):
    """
    Функция возвращает ссылку на фото максимального размера и размер фото
    """
    max_size = 0
    needed_elem = 0
    for i in range(len(photo)):
        size = photo[i].get('width') * photo[i].get('height')
        if size > max_size:
            max_size = size
            needed_elem = i
    return photo[needed_elem].get('url'), photo[needed_elem].get('type')

class Vk:
    def __init__(self, token_list, version='5.131'):
        """
        Метод для получения параметров по умолчанию для запроса VK
        """
        self.token = token_list[0]
        self.id = token_list[1]
        self.version = version
        self.start_params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self.sort_photo_params()

    def photo_info(self):
        """
        Метод для получения количества фотографий по заданным параметрам
        """
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1,
                  'rev': 1
                  }
        res = requests.get(url, params={**self.start_params, **params}).json()['response']
        return res['count'], res['items']

    def photo_params(self):
        """
        Метод для получения словаря с параметрами фотографий
        """
        photo_count, photo_items = self.photo_info()
        result = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = max_size_photo(photo_items[i]['sizes'])
            new_value = result.get(likes_count, [])
            new_value.append({'likes_count': likes_count,
                              'add_name': likes_count,
                              'url_picture': url_download,
                              'size': picture_size})
            result[likes_count] = new_value
        return result

    def sort_photo_params(self):
        """
        Метод для получения словаря с параметрами фотографий и списка json
        """
        json_list = []
        sorted_dict = {}
        photo_dict = self.photo_params()
        counter = 0
        for i in photo_dict.keys():
            for value in photo_dict[i]:
                if len(photo_dict[i]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                else:
                    file_name = f'{value["likes_count"]} {value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                if value["likes_count"] == 0:
                    sorted_dict[file_name] = photo_dict[i][counter]['url_picture']
                    counter += 1
                else:
                    sorted_dict[file_name] = photo_dict[i][0]['url_picture']
        return json_list, sorted_dict


class Yadi:
    def __init__(self, folder_name, token_list, num=5):
        """
        Метод для получения параметров по умолчанию для загрузки фотографий
        """
        self.token = token_list[0]
        self.added_files_num = num
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.headers = {'Authorization': self.token}
        self.folder = self.create_folder(folder_name)

    def create_folder(self, folder_name):
        """
        Метод для создания папки на яндекс диске для загрузки фотографий
        """
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка {folder_name} создана.\n')
        else:
            print(f'\nПапка {folder_name} уже существует.\n')
        return folder_name

    def upload_url(self, folder_name):
        """
        Метод для получения ссылки для загрузки фотографий
        """
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        res = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        upload_url = []
        for i in res:
            upload_url.append(i['name'])
        return upload_url

    def create_copy(self, dict_files):
        """
        Метод загрузки фотографий на Я-диск
        """
        files_in_folder = self.upload_url(self.folder)
        counter = 0
        for key, i in zip(dict_files.keys(), tqdm(range(self.added_files_num))):
            if counter < self.added_files_num:
                if key not in files_in_folder:
                    params = {'path': f'{self.folder}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    counter += 1
                else:
                    print(f'Внимание:Файл {key} уже существует')
            else:
                break

        print(f'\nЗапрос завершен, новых файлов скопировано (по умолчанию: 5): {counter}'
              f'\nВсего файлов в исходном альбоме VK: {len(dict_files)}')


if __name__ == '__main__':

    tokenVK = 'VK_token.txt'  # токен и id доступа хранятся в файле (построчно)
    tokenYandex = 'ya_disk_token.txt'  # хранится только токен яндекс диска

    my_VK = Vk(token_vk(tokenVK))  # Получение JSON списка с информацией о фотографииях

    with open('json_file.json', 'w') as f:  # Сохранение JSON списка в файл my_VK_photo.json
        json.dump(my_VK.json, f)

    # Создаем экземпляр класса Yandex с параметрами: "Имя папки", "Токен" и количество скачиваемых файлов
    my_yandex = Yadi('"NEW FOLDER"', token_vk(tokenYandex), 5)
    my_yandex.create_copy(my_VK.export_dict)  # Вызываем метод create_copy для копирования фотографий с VK на Я-диск