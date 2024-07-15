import logging

import requests

from text import *
from config import *
from DEB import get_user_data

from text import system_content


def create_system_prompt(user_id: int) -> str:
    prompt = system_content
    user_data = get_user_data(user_id)
    prompt += (f'Напиши начало истории в стиле {user_data["genre"]}, в роли главного героя: {user_data["hero"]}. '
               f'Сеттинг здесь это {user_data["setting"]} \n')
    if user_data['additions']:
        prompt += f'Также пользователь просит учесть эту дополнительную информацию: {user_data["additions"]}'
    prompt += 'Не давай никакие подсказки пользователю от себя, он знает что делать.'
    return prompt


def ask_gpt(user_id: int, mode: str = 'continue') -> str:
    user_data = get_user_data(user_id)
    user_collection = user_data['messages']
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": TEMPERATURE,
            "maxTokens": MAX_TOKENS
        },
        "messages": []
    }
    for row in user_collection:
        content = row['text']
        if mode == 'continue' and row['role'] == 'user':
            content += '\n' + cont
        elif mode == 'end' and row['role'] == 'user':
            content += '\n' + end
        data['messages'].append({'role': row['role'], 'text': content})
    response = requests.post(URL, headers=headers, json=data)

    if response.status_code != 200:
        result = f'Ошибка! Статус кода: {response.status_code}'
        logging.debug(f'Ошибка при получении ответа от GPT')
        return result
    result = response.json()["result"]["alternatives"][0]["message"]["text"]
    return result


def count_tokens_in_dialogue(messages: list) -> int:
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
       "maxTokens": MAX_TOKENS,
       "messages": []
    }

    for row in messages:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["text"]
            }
        )

    return len(requests.post(URL, json=data, headers=headers).json()["tokens"])

def promt(system_content , a ,assistant_content , answer):
    try:

        headers = {
            'Authorization': f'Bearer {IAM_TOKEN}',
            'Content-Type': 'application/json'
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": 200

            },
            "messages": [
                {
                    "role": "user",
                    "text": system_content + a + assistant_content + answer
                }
            ]
        }
        response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                                 headers=headers,
                                 json=data)

        if response.status_code == 200:
            text = response.json()["result"]["alternatives"][0]["message"]["text"]
            return text
        else:
            raise RuntimeError(
                'Invalid response received: code: {}, message: {}'.format(
                    {response.status_code}, {response.text}
                )
            )

    except Exception as e:
            error_gpt1 = 'Произошла ошибка!'
            logging.error(str(e))
            return error_gpt1