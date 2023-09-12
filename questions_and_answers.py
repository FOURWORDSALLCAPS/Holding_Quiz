import re


def get_questions_and_answers(file_path):
    with open(file_path, 'r', encoding='KOI8-R') as file:
        file_content = file.read()
    file_content_split = file_content.split('\n\n')
    questions = []
    answers = []
    for line in file_content_split:
        if 'Вопрос' in line:
            questions.append(line)
        elif 'Ответ' in line:
            answers.append(line)
    questions_answers = dict(zip(questions, answers))

    return questions_answers


def get_answer(user_answer):
    answer = user_answer.replace('Ответ:\n', '')
    if '(' in answer:
        answer = re.sub(r'\([^)]*\)', '', answer)
    period_position = answer.find('.')
    if period_position != -1:
        answer = answer[:period_position].strip()
    answer = answer.replace('\n', ' ').replace('  ', ' ')

    return answer
