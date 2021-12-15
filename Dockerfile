FROM qmiinhh/auto-calling-worker:base

LABEL maintainer="minhnq49@ghtk.co"

# Create directory
WORKDIR /auto_call
COPY . /auto_call
COPY ./run.sh /run.sh
# Pip install
RUN pip3 install --upgrade pip cmake
RUN pip3 install -r requirements.txt
RUN pip3 install pytgvoip-pyrogram
RUN chmod +x /run.sh
ENTRYPOINT [ "/run.sh" ]

