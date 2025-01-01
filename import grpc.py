import grpc
import time

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        # Burada mevcut bir gRPC servisine bağlanmaya çalışın
        pass

if __name__ == '__main__':
    run()
