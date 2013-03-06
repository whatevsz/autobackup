import networkConnection
import subprocess
import idGenerator
import fdManager
import time

class SSHNetworkConnection(networkConnection.NetworkConnection):
    
    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        
        
        self.__sshProcess = None
        
    def __del__(self):
        pass
        # At this point, the object may already be deleted and disconnect may not be found.
        #self.diconnect()
    
    def connect(self, user, timeout, remoteShell):
        if self.__sshProcess != None:
            return 
         
        connectionID = idGenerator.generateID(20)
        
        args = ["ssh",\
                "-o", "StrictHostKeyChecking=yes",\
                "-p", str(self.__port),\
                "-q",\
                "-x",\
                "-l", user,\
                self.__host.ip,\
                # Double quotes will automatically be added by subprocess.list2cmdline()
                'echo {0} ; {1}'.format(connectionID, remoteShell)]
                                       
        self.__sshProcess = subprocess.Popen(args, shell=False, bufsize=-1,\
                                             stdout=subprocess.PIPE,\
                                             stderr=subprocess.PIPE,\
                                             stdin=subprocess.PIPE)        

        
        # We will poll the process output once every 100 ms 
        POLL_INTERVAL = 100
        maxPolls = timeout / POLL_INTERVAL
        poll = 0
        
        # 0: stdout, 1: stderr
        stdpipe = (self.__sshProcess.stdout, self.__sshProcess.stderr)
        output = [[],[]]
        lines = [[],[]]
        
        # Unblock pipes so read() and readline() does not block
        for i in 0,1:
            fdManager.unblockFileDescriptor(stdpipe[i])
        
        connected = False

        # Now we will wait for a line in stdout starting with connectionID or abort when timeout is exceeded
        while True:
            poll = poll + 1
            
            if poll >= maxPolls:
                self.disconnect()
                raise Exception("timeout")
                        
            for i in 0,1:
                lines[i] = fdManager.readAll(stdpipe[i])
                                
            for i in 0,1:
                for line in lines[i].split("\n"):
                    if line:
                        output[i].append(line)

            for line in lines[0].split("\n"):
                if line.startswith(connectionID):
                    # Connection established
                    connected = True
                    
            if connected:
                break
            
            time.sleep(POLL_INTERVAL/1000.0)
            
        for i in 0,1:
            output[i].append(fdManager.readAll(stdpipe[i]))
            output[i] = "".join(output[i])
            
        if output[1]:
            raise Exception("Some error orrcured, stderr:\n{0}".format(output[1]))
        
        return (output[0],output[1])
    
         
     
    def disconnect(self):
        if self.__sshProcess != None:
            self.__sshProcess.terminate()
            self.__sshProcess = None    
    
    def execute(self, command, timeout):
        commandID = idGenerator.generateID(20)
        stdpipe = (self.__sshProcess.stdout, self.__sshProcess.stderr)
        
        # Flush streams as precaution
        for i in 0,1:
            stdpipe[i].flush()
                         
        output = [[],[]]
        lines = [[],[]]
        
        lastLine = None
        finished = False
        
        POLL_INTERVAL = 1000
        maxPolls = timeout / POLL_INTERVAL
        polls = 0
 
                     
        command = '{0} ; echo {1}@$?\n'.format(command, commandID)
        self.__sshProcess.stdin.write(command)
        self.__sshProcess.stdin.flush()
        
        while True:
            polls = polls + 1

            if polls >= maxPolls:
                raise Exception("timeout")
                                    
            for i in 0,1:
                lines[i] = fdManager.readAll(stdpipe[i])
                            
            for i in 0,1:
                for line in lines[i].split("\n"):
                    if i == 0 and line.startswith(commandID):
                        lastLine = line
                        finished = True
                    elif line:
                        output[i].append(line)

                    
            if finished:
                break
            time.sleep(POLL_INTERVAL/1000.0)
            
        for i in 0,1:
            output[i].append(fdManager.readAll(stdpipe[i]))
            output[i] = "\n".join(output[i])
            
        exitCode = lastLine.split("@")[1]
                            
        return(exitCode, output[0], output[1])


    def isConnected(self):
        return self.__sshProcess != None

















  