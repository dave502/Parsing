import requests
import json


class GitApiRequests:
    __url = 'https://api.github.com/'
    __parameters = {
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
        }
    __save_response_to_file = True

    def __init__(self, user='dave502'):
        self.__default_user = user

    def __input_user_name(self):
        return str(input('Please enter user name or leave empty for default user ' +
                         self.__default_user + ': ') or self.__default_user)

    def get_user_repos(self) -> list:
        """Returns list of user's repositories"""
        user = self.__input_user_name()
        request_url = self.__url + 'users/' + user + '/repos'
        response = requests.get(request_url, params=self.__parameters)
        if response.ok:
            j_response = response.json()
            if self.__save_response_to_file:
                with open('response.json', 'w') as file:
                    json.dump(j_response, file, indent=4)
            result = [x['html_url'] for x in j_response]
            return result
        else:
            return ['Request fault with code ' + str(response.status_code)]


git_api = GitApiRequests()
print(*git_api.get_user_repos(), sep='\n')
