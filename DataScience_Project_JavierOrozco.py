#!/usr/bin/env python
# coding: utf-8

# In[11]:


import calendar 
import json 
import random 
from datetime import date, timedelta 
import numpy as np 
from delorean import parse 
import pandas as pd 
import faker


# In[13]:


fake = faker.Faker()


# In[15]:


usernames = set()
usernames_no = 1000
# populate the set with 1000 unique usernames
while len(usernames) < usernames_no:
    usernames.add(fake.user_name())


# In[17]:


def get_random_name_and_gender():
    skew = 0.6 # 60% of users will be female
    male = random.random() > skew
    if male :
        return fake.name_male(), 'M'
    else:
        return fake.name_female(), 'F'

def get_users(usernames):
    users = []
    for username in usernames:
        name, gender = get_random_name_and_gender()
        user = {
            'username': username,
            'name': name,
            'gender': gender,
            'email': fake.email(),
            'age': fake.random_int(min=18, max=90),
            'address': fake.address(),
            }
        users.append(json.dumps(user))
    return users

users = get_users(usernames)
users[:3]


# In[23]:


# campaign name format:
# InternalType_StartDate_EndDate_TargetAge_TargetGender_Currency
def get_type():
    types = ['AKX', 'BYU', 'GRZ', 'KTR']
    return random.choice(types)

def get_start_end_dates():
    duration = random.randint(1, 2 * 365)
    offset = random.randint(-365, 365)
    start = date.today() - timedelta(days=offset)
    end = start + timedelta(days=duration)
    
    def _format_date(date_):
        return date_.strftime("%Y%m%d")
    return _format_date(start), _format_date(end)

def get_age():
    age = random.randint(20, 45)
    age -= age % 5
    diff = random.randint(5, 25)
    diff -= diff % 5
    return '{}-{}'.format(age, age + diff)

def get_gender():
    return random.choice(('M', 'F', 'B'))

def get_currency():
    return random.choice(('GBP', 'EUR', 'USD'))

def get_campaign_name():
    separator = '_'
    type_ = get_type()
    start_end = separator.join(get_start_end_dates())
    age = get_age()
    gender = get_gender()
    currency = get_currency()
    return separator.join(
            (type_, start_end, age, gender, currency))
    
    


# In[18]:


# campaign name format:
# InternalType_StartDate_EndDate_TargetAge_TargetGender_Currency
def get_campaign_data():
    name = get_campaign_name()
    budget = random.randint(10**3,10**6)
    spent = random.randint(10**2,budget)
    clicks = int(random.triangular(10**2, 10**5, 0.2 * 10**5))
    impressions = int(random.gauss(0.5 * 10**6, 2))
    return {
        'cmp_name': name,
        'cmp_bgt': budget,
        'cmp_spent': spent,
        'cmp_clicks': clicks,
        'cmp_impr': impressions
        }
    


# In[19]:


def get_data(users):
    data = []
    for user in users:
        campaigns = [get_campaign_data()
                    for _ in range(random.randint(2, 8))]
        data.append({'user': user, 'campaigns': campaigns})
    return data


# In[24]:


rough_data = get_data(users)
rough_data[:2] # let's take a peek


# In[25]:


data = []
for datum in rough_data:
    for campaign in datum['campaigns']:
        campaign.update({'user': datum['user']})
        data.append(campaign)

data[:2]


# In[28]:


df = pd.DataFrame(data)
df.head()


# In[30]:


df.count()


# In[31]:


df.describe()


# In[36]:


df['cmp_bgt'].sort_index(ascending = False).head(3)


# In[37]:


df['cmp_bgt'].sort_index(ascending = False).tail(3)


# In[39]:


def unpack_campaign_name(name):
    # very optimistic method, assumes data in campaign name
    # is always in good state
    type_, start, end, age, gender, currency = name.split('_')
    start = parse(start).date
    end = parse(end).date
    return type_, start, end, age, gender, currency

campaign_data = df['cmp_name'].apply(unpack_campaign_name)
campaign_cols = ['Type', 'Start', 'End', 'Age', 'Gender', 'Currency']
campaign_df = pd.DataFrame(
                campaign_data.tolist(), columns=campaign_cols, index=df.index)

campaign_df.head(3)


# In[40]:


df = df.join(campaign_df)


# In[41]:


df[['cmp_name'] + campaign_cols].head(3)  


# In[42]:


def unpack_user_json(user):
    # very optimistic as well, expects user objects
    # to have all attributes
    user = json.loads(user.strip())
    return [
        user['username'],
        user['email'],
        user['name'],
        user['gender'],
        user['age'],
        user['address'],
        ]

user_data = df['user'].apply(unpack_user_json)
user_cols = ['username', 'email', 'name', 'gender', 'age', 'address']
user_df = pd.DataFrame(
            user_data.tolist(), columns=user_cols, index=df.index)


# In[46]:


df[['user'] + user_cols].head(2)    


# In[47]:


df.columns


# In[48]:


better_columns = ['Budget', 'Clicks', 'Impressions',
'cmp_name', 'Spent', 'user','Type', 'Start', 'End',
'Target Age', 'Target Gender', 'Currency',
'Username', 'Email', 'Name',
'Gender', 'Age', 'Address']

df.columns = better_columns 


# In[49]:


def calculate_extra_columns(df):
    # Click Through Rate
    df['CTR'] = df['Clicks'] / df['Impressions']
    # Cost Per Click
    df['CPC'] = df['Spent'] / df['Clicks']
    # Cost Per Impression
    df['CPI'] = df['Spent'] / df['Impressions']

calculate_extra_columns(df)


# In[50]:


df[['Spent', 'Clicks', 'Impressions','CTR', 'CPC', 'CPI']].head(3)


# In[51]:


#We manually verify the accuracy of the results 
clicks = df['Clicks'][0]
impressions = df['Impressions'][0]
spent = df['Spent'][0]
CTR = df['CTR'][0]
CPC = df['CPC'][0]
CPI = df['CPI'][0]
print('CTR:', CTR, clicks / impressions)
print('CPC:', CPC, spent / clicks)
print('CPI:', CPI, spent / impressions)


# In[52]:


def get_day_of_the_week(day):
    number_to_day = dict(enumerate(calendar.day_name, 1))
    return number_to_day[day.isoweekday()]
def get_duration(row):
    return (row['End'] - row['Start']).days

df['Day of Week'] = df['Start'].apply(get_day_of_the_week)
df['Duration'] = df.apply(get_duration, axis=1)


# In[53]:


df['Start']


# In[54]:


df[['Start', 'End', 'Duration', 'Day of Week']].head(3)   


# In[55]:


final_columns = ['Type', 'Start', 'End', 'Duration', 'Day of Week', 'Budget',
'Currency', 'Clicks', 'Impressions', 'Spent', 'CTR', 'CPC',
'CPI', 'Target Age', 'Target Gender', 'Username', 'Email',
'Name', 'Gender', 'Age']
df = df[final_columns]


# In[56]:


df.to_csv('df.csv')


# In[57]:


df.to_json('df.json')


# In[61]:


get_ipython().run_line_magic('matplotlib', 'inline')


# In[70]:


import pylab
pylab.rcParams.update({'font.family' : 'serif'})


# In[84]:


df.describe()


# In[71]:


df[['Spent', 'Clicks', 'Impressions','Budget']].hist(bins=16, figsize=(16, 6));


# In[74]:


df[['CTR', 'CPC', 'CPI']].hist(bins=20, figsize=(16, 6));


# In[85]:


df.info()

