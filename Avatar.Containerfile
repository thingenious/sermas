FROM ubuntu:24.04

ENV DEBIAN_FRONTEND="noninteractive"
ENV DEBCONF_NONINTERACTIVE_SEEN=true

# Install dependencies
RUN apt update && \
    apt install -y \
    build-essential \
    tini \
    curl \
    dotnet8 \
    dotnet-sdk-8.0 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*

WORKDIR /app

COPY avatar /app

RUN useradd -m user && \
    chown -R user:user /app


RUN dotnet restore
RUN dotnet build AliveOnD-ID.sln -c Release
RUN dotnet publish AliveOnD-ID.csproj -c Release --self-contained true -o /app/publish

EXPOSE 5000
ENV TINI_SUBREAPER=true
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD [ "/app/publish/AliveOnD-ID" ]
