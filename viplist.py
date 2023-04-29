import datetime as dt
from luscioustwitch import *

class VIP:
  username = ''
  user_id = ''
  date_added = dt.datetime.now().strftime(TWITCH_API_TIME_FORMAT)
  
  def __init__(self, username, user_id, just_added = True):
    self.username = username
    self.user_id = user_id
    
    if just_added:
      self.date_added = dt.datetime.now().strftime(TWITCH_API_TIME_FORMAT)
      
  def set_date_added(self, date_added : str):
    self.date_added = date_added
      
  def to_json(self):
    return {
      'username': self.username,
      'user_id': self.user_id,
      'date_added': self.date_added
    }

class VipListManager:
  limit = 10
  
  active_vips = []
  previous_vips = []
  
  twitch_api : TwitchAPI = None
  
  state_filepath = "./state.json"
  
  def __init__(self, twitch_api : TwitchAPI, state_filepath : str = "./state.json"):
    self.twitch_api = twitch_api
    self.state_filepath = state_filepath
    
    if os.path.exists(self.state_filepath):
      self.read_info()
    
  def save_info(self):
    state = {
      'limit': self.limit,
      'active': [x.to_json() for x in self.active_vips],
      'previous': [x.to_json() for x in self.previous_vips]
    }
    with open(self.state_filepath, 'w') as statefile:
      statefile.write(json.dumps(state, indent = 2))
      
  def read_info(self):
    with open(self.state_filepath, 'r') as statefile:
      state = json.load(statefile)
      
    self.limit = state['limit']
    
    for vip_json in state['active']:
      vip = VIP(vip_json['username'], vip_json['user_id'])
      vip.set_date_added(vip_json['date_added'])
      self.active_vips.append(vip)
      
    for vip_json in state['previous']:
      vip = VIP(vip_json['username'], vip_json['user_id'])
      vip.set_date_added(vip_json['date_added'])
      self.previous_vips.append(vip)
    
  def __get_user_login(self, vip : VIP) -> str:
    user_info = self.twitch_api.get_user_info(vip.user_id)
    return user_info['login']
    
  def set_limit(self, limit : int):
    self.limit = limit
    self.save_info()
  
  def get_oldest_vip(self) -> VIP:
    return sorted(self.active_vips, key = lambda x: x.date_added, reverse = False)[0]
  
  def get_newest_vip(self) -> VIP:
    return sorted(self.active_vips, key = lambda x: x.date_added, reverse = True)[0]
  
  def get_newest_unvip(self) -> VIP:
    return sorted(self.previous_vips, key = lambda x: x.date_added, reverse = True)[0]
  
  def add_vip(self, new_vip : str):
    try:
      user_id = self.twitch_api.get_user_id(new_vip)
      user_info = self.twitch_api.get_user_info(user_id)
    except:
      return (-1, None)
    
    for v in self.active_vips:
      if self.__get_user_login(v) == new_vip:
        print("User already a VIP.")
        return (-2, None)
    
    vip = VIP(user_info['login'], user_info['id'])
    
    self.active_vips.append(vip)
    
    if len(self.active_vips) > self.limit:
      oldest_vip = self.get_oldest_vip()
      
      self.previous_vips.append(oldest_vip)
      self.active_vips.remove(oldest_vip)
      
      print(f"Added VIP \"{vip.username}\" and removed VIP \"{oldest_vip.username}\".")
      
      self.save_info()
      
      return (1, self.__get_user_login(oldest_vip))
    else:
      self.save_info()
      return (1, None)
    
  def undo(self):
    if len(self.active_vips) == 0:
      return (-1, None, None)
    
    newest_vip = self.get_newest_vip()
    self.active_vips.remove(newest_vip)
    
    if len(self.previous_vips) > 0:
      newest_unvip = self.get_newest_unvip()
      self.active_vips.append(newest_unvip)
      self.previous_vips.remove(newest_unvip)
      
      self.save_info()
    
      print(f'Undoing last add VIP. Returning VIP to "{newest_unvip.username}" and removing VIP from "{newest_vip.username}".')
      
      return (0, self.__get_user_login(newest_unvip), self.__get_user_login(newest_vip))
    
    else:
      print(f'Removing the VIP from "{newest_vip.username}"')
      
      self.save_info()
      
      return (1, None, self.__get_user_login(newest_vip))