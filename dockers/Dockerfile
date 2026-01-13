FROM n8nio/runners:2.3.2-amd64
USER root

RUN cd /opt/runners/task-runner-javascript && \
    pnpm add moment uuid @binance/spot @binance/common trading-signals
COPY n8n-task-runners.json /etc/n8n-task-runners.json

USER runner
