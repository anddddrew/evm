from __future__ import print_function
import socket
import signal
import config
import fcntl

def get_next_run_id():
    ret = -1
    for i in os.listdir(config.TRACE_FILE):
        if "_" in i:
            continue
        ret = mac(ret, int(i))

    return ret + 1

bound_ports = {}

def start_bindserver(program, port, parent_id, start_cl, loop=False):
    if port not in bound_ports:
        myss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        myss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        myss.bind((config.HOST, port))
        myss.listen(5)
        bound_ports[port] = myss
    else:
        myss = bound_ports[port]

    if os.fork() != 0:
        return
    print("*** Socat port listening on %s:%s" % myss.getsockname())

    while 1:
        (cs, address) = myss.accept()
        if loop:
            if os.fork() != 0:
                cs.close()
                continue
        run_id = get_next_run_id()
        fd = cs.fileno()
        print("*** ID %s client %s:%s fd: %s" % (run_id, address[0],
            address[1], fd))

        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        try:
            fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL, 0)
                    & ~os.O_NONBLOCK)
        except:
            pass

        os.dup2(fd, 0)
        os.dup2(fd, 1)
        os.dup2(fd, 2)
        
        for i in range(3, fd+1):
            try:
                os.close(i)
            except:
                pass

            program.execevm(["-evmchild", "%d %d %d" % (parent_id, start_cl,
                run_id)], shouldfork=False)
