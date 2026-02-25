# encoding: utf-8

from __future__ import annotations

from urllib.parse import urlencode
from typing import Any, Optional, cast, List, Tuple

from flask import Blueprint, make_response, abort, redirect, request

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.search as search
from ckan.lib.helpers import helper_functions as h
from ckan.types import ActionResult, Context, DataDict, Query, Schema
from ckan.common import g, config, current_user, _



CACHE_PARAMETERS = [u'__cache', u'__no_cache__']


estadistica = Blueprint(u'estadistica', __name__)


def form() -> str:
     
    u''' display about page'''
   
    return base.render(u'estadistica/form.html')


def powerbi() -> str:
     
    u''' display about page'''
   
    return base.render(u'estadistica/powerbi.html')
    
def powerbi_1() -> str:
     
    u''' display about page'''
   
    return base.render(u'estadistica/powerbi_1.html')

def powerbi_2() -> str:
     
    u''' display about page'''
   
    return base.render(u'estadistica/powerbi_2.html')    



def redirect_locale(target_locale: str, path: Optional[str] = None) -> Any:

    target = f'/{target_locale}/{path}' if path else f'/{target_locale}'

    if request.args:
        target += f'?{urlencode(request.args)}'

    return redirect(target, code=308)

util_rules: List[Tuple[str, Any]] = [
    (u'/encuenta', form),
    (u'/estadistica', powerbi),
    (u'/estadistica', powerbi_1),
    (u'/estadistica', powerbi_2)
    ]
for rule, view_func in util_rules:
    estadistica.add_url_rule(rule, view_func=view_func)

locales_mapping: List[Tuple[str, str]] = [
    ('zh_TW', 'zh_Hant_TW'),
    ('zh_CN', 'zh_Hans_CN'),
    ('no', 'nb_NO'),
]

for locale in locales_mapping:

    legacy_locale = locale[0]
    new_locale = locale[1]

    estadistica.add_url_rule(
        f'/{legacy_locale}/',
        view_func=redirect_locale,
        defaults={'target_locale': new_locale}
    )

    estadistica.add_url_rule(
        f'/{legacy_locale}/<path:path>',
        view_func=redirect_locale,
        defaults={'target_locale': new_locale}
    )    