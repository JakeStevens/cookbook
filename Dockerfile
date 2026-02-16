FROM docker.io/library/nginx:alpine
COPY cookbook/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
