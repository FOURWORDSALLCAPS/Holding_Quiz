def get_questions_and_answers():
    with open('quiz_questions/ierusa11.txt', 'r', encoding='KOI8-R') as file:
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


if __name__ == '__main__':
    get_questions_and_answers()
