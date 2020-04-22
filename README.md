项目简介

    统计项目的qps，rt，非200请求
    原理 通过将数据（key，value，时间戳）打到graphite（2003接口）-》grafana 帮忙统计
    正则按行读取日志文件，逐行解析统计发送请求统计
    
    日志文件会自动根据时间将前面部分切割，日志不断写入该文件，程序不停统计按照秒统计的qps数据，然后发送到目标时序数据库

Notice
    
    log_format  main  '[$time_local] $uri $status $request_time [$upstream_addr] [$upstream_response_time] [$upstream_status] "127.0.0.1" $body_bytes_sent "$http_referer" $args "$request_body" "exp_bucketid"';
    日志格式为 [22/Apr/2020:15:06:03 +0800] /trends/gateway 200 0.000 [-] [-] [-] "127.0.0.1" 13 "-" - "-" "exp_bucketid"
    
    可自定义日志格式且修改对应的日志解析方法，修改统计方法即可使用
    
    graphite和grafana安装
    
    graphate docker 启动安装
    0.wget https://github.com/graphite-project/docker-graphite-statsd/archive/master.zip
    1.docker run -d --name graphite --restart=always -p 1808:80 -p 2003-2004:2003-2004 -p 2023-2024:2023-2024 -p 8125:8125/udp -p 8126:8126 graphiteapp/graphite-statsd
    3.linux 有时候安装有问题请 yum update 然后systemctl restart docker
    
    grafana 安装
    
       0  wget https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana-3.1.1-1470047149.x86_64.rpm
       1  sudo yum install grafana-3.1.1-1470047149.x86_64.rpm
       2  serivce grafana-server start
       3  ststemctl strat grafana-server
       4  sudo /bin/systemctl start grafana-server.service
       5  grafana-cli plugins list-remote
       6  grafana-cli plugins install alexanderzobnin-zabbix-app
       7  service grafana-server restart
       8  grafana-cli plugins install grafana-piechart-panel
   