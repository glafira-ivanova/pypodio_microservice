# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter
from pypodio2 import api
from . import client_settings


logging.basicConfig(format=u'[%(asctime)s] %(message)s', level=logging.DEBUG, filename=client_settings.log_file)


def mediaplan_for_humans(mediaplan):
    res = {}
    for field in mediaplan['fields']:
        res['mp_id'] = mediaplan['item_id']
        name = field['label']
        if name in ['Name', 'Status']:
            res[name] = field['values'][0]['value']['text']
        elif name == 'Account Manager':
            res[name] = field['values'][0]['value']
        elif name == 'Date':
            res[name] = datetime.strptime(field['values'][0]['start_date_utc'], '%Y-%m-%d')
    return res


def campaign_for_humans(campaign):
    res = {}
    for field in campaign['fields']:
        name = field['label']
        if name in ['Status', 'Category']:
            res[name] = field['values'][0]['value']['text']
        elif name == 'Campaign Name':
            res[name] = field['values'][0]['value']
        elif name == 'Period':
            res[name] = datetime.strptime(field['values'][0]['start_date_utc'], '%Y-%m-%d')
        elif name == 'Mediaplan':
            res[name] = field['values'][0]['value']['item_id']
    return res


def calc_statistic(mediaplans, campaigns):
    res = {}
    mediaplan_detail = [mediaplan_for_humans(mp) for mp in mediaplans]
    confirmed_last_ninety_days = [mp for mp in mediaplan_detail if mp['Status'] == 'Confirmed' and
                                  mp['Date'] <= (datetime.today() - relativedelta(days=90))]
    mp_per_acc_manager = Counter()
    for mp in confirmed_last_ninety_days:
        acc_manager = re.findall(r'<p>(.+)</p>', mp['Account Manager'])[0]
        mp_per_acc_manager[acc_manager] += 1
    res.update({
        'mp_per_acc_manager': mp_per_acc_manager,
    })

    campaign_detail = [campaign_for_humans(camp) for camp in campaigns]
    active_desktop = [camp for camp in campaign_detail if camp['Status'] == 'Active' and
                      camp['Category'] == 'Desktop']
    mediaplans_with_campaign = {camp['Mediaplan'] for camp in active_desktop}
    res.update({
        'mediaplans_with_campaign': len(mediaplans_with_campaign)
    })
    converted_mediaplans = {mp['mp_id'] for mp in confirmed_last_ninety_days if mp['mp_id'] in mediaplans_with_campaign}
    converted_mp_percentage = len(converted_mediaplans) / len(mediaplans)
    res.update({
        'converted_mp_percentage': converted_mp_percentage,
    })
    return res


def form_letter(stats):
    accout_manager_block = 'Аккаунт-менеджер, Количество медиапланов:\n'
    for k, v in stats['mp_per_acc_manager'].items():
        accout_manager_block += '{}, {} \n'.format(k, v)
    text = '''
        Количество медиапланов по аккаунт-менеджеру:
        {}
        Количество медиапланов со связкой с кампанией: {}
        Отношение конвертированных медиапланов к общему количеству(конверсия): {}'''.format(accout_manager_block,
                                                                                            stats['mediaplans_with_campaign'],
                                                                                            stats['converted_mp_percentage'],
                                                                                            )
    return text


def main():
    API = api.OAuthClient(client_settings.client_id, client_settings.client_secret, client_settings.username,
                          client_settings.password)
    for org in API.Org.get_all():
        logging.info(org['url'])
        for space in API.Space.find_all_for_org(org['org_id']):
            logging.info(space['url'])
            apps = {}
            for app in API.Application.list_in_space(space['space_id']):
                logging.info(app['url'])
                items = API.Application.get_items(app['app_id'], limit=500)
                apps[app['config']['name']] = items['items']
                for item in items['items']:
                    logging.info(item['link'])
            if apps.get('Mediaplan') and apps.get('Campaign'):
                stats = calc_statistic(apps.get('Mediaplan'), apps.get('Campaign'))
                return stats


if __name__ == '__main__':
    stats = main()
    letter_body = form_letter(stats)
    # Do something with letter body

