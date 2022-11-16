from django.core.validators import RegexValidator


class OnlyLettersValidator(RegexValidator):
    regex = r'^\D*$'
    message = ('Поля имя и фамилия не должны содержать числа')
