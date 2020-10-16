FROM ubuntu:18.04

LABEL maintainer="alexanderbaranof@gmail.com"

# Настройки для сборки Ubuntu
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Устанавливаем зависимости
RUN apt update
RUN apt install -y git
RUN apt install -y p7zip-full
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y htop
RUN pip3 install flask
RUN pip3 install openpyxl
RUN pip3 install requests
RUN pip3 install gevent

# Задаем рабочую папку
WORKDIR /home/flask_app/

# Копируем все содержание текущего каталога в рабочую папку
COPY . .

# Команда при запуске
RUN chmod +x /home/flask_app/run_system.sh
CMD ["/home/flask_app/run_system.sh"]

# Открываем порты
EXPOSE 80
EXPOSE 443