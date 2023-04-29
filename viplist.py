import datetime as dt
from luscioustwitch import *

class VIP:
  username = ''
  user_id = ''
  date_added = dt.datetime.now()
  
  def __init__(self, username, user_id, just_added = True):
    self.username = username
    self.user_id = user_id
    
    if just_added:
      self.date_added = dt.datetime.now()
      
  def to_json(self):
    return {
      'username': self.username,
      'user_id': self.user_id,
      'date_added': self.date_added.strftime(TWITCH_API_TIME_FORMAT)
    }

class VipListManager:
  limit = 10
  
  active_vips = []
  previous_vips = []
  
  twitch_api : TwitchAPI = None
  
  def __init__(self, twitch_api : TwitchAPI):
    self.twitch_api = twitch_api
    
  def __get_user_login(self, vip : VIP) -> str:
    user_info = self.twitch_api.get_user_info(vip.user_id)
    return user_info['login']
    
  def set_limit(self, limit : int):
    self.limit = limit
  
  def get_oldest_vip(self) -> VIP:
    return sorted(self.active_vips, key = lambda x: x.date_added, reverse = True)[0]
  
  def get_newest_vip(self) -> VIP:
    return sorted(self.active_vips, key = lambda x: x.date_added, reverse = False)[0]
  
  def get_newest_unvip(self) -> VIP:
    return sorted(self.previous_vips, key = lambda x: x.date_added, reverse = False)[0]
  
  def add_vip(self, new_vip : str) -> str:
    user_id = self.twitch_api.get_user_id(new_vip)
    user_info = self.twitch_api.get_user_info(user_id)
    
    vip = VIP(user_info['login'], user_info['id'])
    
    self.active_vips.append(vip)
    
    if len(self.active_vips) > self.limit:
      oldest_vip = self.get_oldest_vip()
      
      self.previous_vips.append(oldest_vip)
      self.active_vips.remove(oldest_vip)
      
      print(f"Added VIP \"{vip.username}\" and removed VIP \"{oldest_vip.username}\".")
      
      return self.__get_user_login(oldest_vip)
    else:
      return None
    
  def undo(self):
    newest_vip = self.get_newest_vip()
    self.active_vips.remove(newest_vip)
    
    if len(self.previous_vips) > 0:
      newest_unvip = self.get_newest_unvip()
      self.active_vips.append(newest_unvip)
    
      print(f'Undoing last add VIP. Returning VIP to "{newest_unvip.username}" and removing VIP from "{newest_vip.username}".')
      
      return (self.__get_user_login(newest_unvip), self.__get_user_login(newest_vip))
    
    else:
      print(f'Removing the VIP from "{newest_vip.username}"')
      return (None, self.__get_user_login(newest_vip))