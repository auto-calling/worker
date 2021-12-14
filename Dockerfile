FROM qmiinhh/auto-calling-worker:base

LABEL maintainer="minhnq49@ghtk.co"

# Create directory
WORKDIR /auto_call
COPY . /auto_call

# Pip install
RUN pip3 install --upgrade pip cmake
RUN pip3 install -r requirements.txt
RUN pip3 install pytgvoip-pyrogram

CMD ["/usr/bin/python3 main.py"]

