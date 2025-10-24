#!/usr/bin/env python3
class TestModule(object):
    def tests(self):
        return {
            'valid_port': self.is_valid_port,
            'safe_user': self.is_safe_user
        }
    
    def is_valid_port(self, port):
        if not isinstance(port, int):
            return False
        return 1024 <= port <= 65535
    
    def is_safe_user (self, username):
        unsafe_user = ['root', 'admin','sudo']
        return username not in unsafe_user and isinstance(username, str)