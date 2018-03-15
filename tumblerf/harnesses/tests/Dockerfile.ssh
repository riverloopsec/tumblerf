FROM corbinu/ssh-server

#ENV TERM xterm

#COPY sshd_config /etc/ssh/sshd_config

#RUN echo -e "testpass\ntestpass" | passwd root
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

COPY test-rsa.key.pub /root/.ssh/authorized_keys

EXPOSE 22

ENTRYPOINT ["ssh-start"]
CMD ["ssh-server"]
