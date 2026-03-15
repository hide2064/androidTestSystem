FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 3000

# nginx はデフォルト80番なので、3000番に変更する設定を追加
RUN sed -i 's/listen\s*80/listen 3000/g' /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
