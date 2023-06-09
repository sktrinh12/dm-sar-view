# pull official base image
FROM node:alpine as build
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV GENERATE_SOURCEMAP=false
ENV CI=false

RUN apk update && apk upgrade --no-cache && \
		apk add --no-cache

# set working directory
WORKDIR /app

# add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# install app dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install 

# add app & build
COPY . ./
RUN npm run build


FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
RUN apk update \
  && apk add curl vim \
  && sed -i '/location \/ {$/a try_files \$uri \/index.html;' /etc/nginx/conf.d/default.conf

EXPOSE 80 
ENTRYPOINT ["nginx", "-g", "daemon off;"]
