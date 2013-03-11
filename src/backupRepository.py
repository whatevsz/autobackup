import event
import apscheduler.scheduler as scheduler # @UnresolvedImport
import datetime

SUFFIX     = 'bak'
# Timeformat used by the datetime.strptime() method of 
TIMEFORMAT = '%Y-%m-%dT%H:%M:%S'

FORMAT     = "{0}.{1}".format(TIMEFORMAT, SUFFIX)

class BackupRepository(object):
    '''
    Represents a backup repository, where a number of backups can be stored. Requires information
    about the expiration of backups and the interval in which backups are to be created. Will raise
    events accordingly.
    '''
    
    def __init__(self, host, path, directories, sourceHost, sources, interval, maxCount, maxAge):
        '''
        :param sourceHost:
        The host of the source directories.
        :param sources:
        A list with absolute pathes to all source directories.
        :param host:
        The host of the repository.
        :param path:
        The absolute path to the repository.
        :param directories:
        The subdirectories of the repository.
        :param interval:
        An timedelta object describing the desired interval between two backups.
        :param maxCount:
        The maximum amount of backups to retain. If this number is exceeded, the oldest
        backups are to be deleted first.
        :param maxAge:
        The maximum age of all backups. Older backups are to be deleted.
        '''
        
        self.__sourceHost = sourceHost
        self.__sources = sources
        
        self.host = host
        self.path = path
        self.__directories = directories
        
        self.__interval = interval
        self.__maxCount = maxCount
        self.__maxAge = maxAge
        
        self.backupExpired = event.Event()
        self.backupRequired = event.Event()
        
        self.__scheduler = scheduler.Scheduler()
        self.__scheduler.add_cron_job(self._minute_elapsed, minute='*')
        self.__scheduler.start()
        
        maxCountAge = maxCount * interval
        self.__maxAge = maxCountAge if maxCountAge > maxAge else maxAge
        

    def _minute_elapsed(self):
        self._check_backups()
    
    
    def _check_backups(self):
        maxBirth = datetime.datetime.now() - self.__maxAge
        minBirth = datetime.datetime.now() - self.__interval
        
        backupNeeded = True
        
        for backup in self.__backups:
            if backup.birth < maxBirth:
                self._on_backup_expired(self.host, backup.directoryName)
            if backup.birth >= minBirth:
                backupNeeded = False
                
        if backupNeeded:
            self._on_backup_required(self.host, self._generate_new_backup_name(), self.__sourceHost, self.__sources)
            
    
    def _initialize_backups(self):
        for directory in self.__directories:
            self.__backups.append(Backup(directory))
            
    def _on_backup_required(self, host, newBackupDirectoryName, sourceHost, sources):
        if len(self.backupRequired):
            self.backupRequired(host, newBackupDirectoryName, sourceHost, sources)
            
    def _on_backup_expired(self, host, expiredBackupDirectoryName):
        if len(self.backupExpired):
            self.backupExpired(host, expiredBackupDirectoryName)
    
    def _generate_new_backup_name(self):
        raise NotImplementedError()
    
    
class Backup(object):
    
    def __init__(self, directoryName):
        self.__directoryName = directoryName
        self.birth = self._get_date(self.__directoryName)

    def _get_date(self, name):
        self.birth = datetime.datetime.strptime(name.split('.')[0])
        
    def _get_directory_name(self):
        return self.__directoryName
    directoryName = property(_get_directory_name)
        