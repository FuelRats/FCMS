# Carrier settings form target
# Also, images!
import colander
import deform
from deform import widget, Form, ValidationFailure
from deform.interfaces import FileUploadTempStore
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed

from ..utils.util import object_as_dict
from ..utils import user as usr, menu, carrier_data
from ..models import Carrier, CarrierExtra, Calendar, Webhook
import logging
import pyramid.httpexceptions as exc
log = logging.getLogger(__name__)


class CarrierSettings(colander.MappingSchema):
    showItinerary = colander.SchemaNode(colander.Boolean(),
                                        widget=widget.CheckboxWidget(template="bootstrap"),
                                        title='Show Itinerary',
                                        description="Show itinerary on public carrier page")
    showMarket = colander.SchemaNode(colander.Boolean(),
                                     widget=widget.CheckboxWidget(template="bootstrap"),
                                     title='Show Market',
                                     description="Show market items on public carrier page")
    showSearch = colander.SchemaNode(colander.Boolean(),
                                     widget=widget.CheckboxWidget(template="bootstrap"),
                                     title="Show on search pages",
                                     description="Show my carrier on Search and Closest pages")


hooktypes = (('discord', 'discord'), ('generic', 'generic'))
tmpstore = FileUploadTempStore()


class CarrierExtraSettings(colander.MappingSchema):
    carrier_image = colander.SchemaNode(deform.FileData(),
                                        widget=widget.FileUploadWidget(tmpstore=tmpstore),
                                        title='Carrier Image',
                                        description="Choose file to upload",
                                        missing=colander.null)
    carrier_motd = colander.SchemaNode(colander.String(),
                                       widget=widget.TextInputWidget(),
                                       description="Set your carrier's Motto / MOTD.",
                                       title="Carrier Motto",
                                       validator=colander.Length(max=150),
                                       missing=colander.null)


class WebhookSchema(colander.Schema):
    hook_url = colander.SchemaNode(colander.String(),
                                   widget=widget.TextInputWidget())
    hook_type = colander.SchemaNode(colander.String(),
                                    widget=widget.SelectWidget(values=hooktypes),
                                    validator=colander.OneOf(('discord', 'generic')))
    enabled = colander.SchemaNode(colander.Boolean(),
                                  widget=widget.CheckboxWidget(template="bootstrap"), required=False)
    jumpEvents = colander.SchemaNode(colander.Boolean(),
                                     widget=widget.CheckboxWidget(template="bootstrap"), required=False)
    marketEvents = colander.SchemaNode(colander.Boolean(),
                                       widget=widget.CheckboxWidget(template="bootstrap"), required=False)
    calendarEvents = colander.SchemaNode(colander.Boolean(),
                                         widget=widget.CheckboxWidget(template="bootstrap"), required=False)
    id = colander.SchemaNode(colander.Integer(),
                             widget=widget.HiddenWidget(),
                             required=False, default=None, missing=colander.drop)
    owner_id = colander.SchemaNode(colander.Integer(),
                                   widget=widget.HiddenWidget(),
                                   required=False, default=None, missing=colander.drop)
    carrier_id = colander.SchemaNode(colander.Integer(),
                                     widget=widget.HiddenWidget(),
                                     required=False, default=None, missing=colander.drop)


class WebhookSequence(colander.SequenceSchema):
    webhooks = WebhookSchema()


class HookSchema(colander.Schema):
    hooks = WebhookSequence()


@view_config(route_name='settings', renderer='../templates/settings.jinja2')
def settings_view(request):
    # Prep schemas and forms
    carrierschema = CarrierSettings().bind(request=request)
    hooksschema = HookSchema().bind(request=request)
    extraschema = CarrierExtraSettings().bind(request=request)

    carrierform = Form(carrierschema, buttons=('submit',), use_ajax=True, formid='carrierform')
    webhookform = Form(hooksschema, buttons=('submit',), use_ajax=True, formid='webhookform')
    extraform = Form(extraschema, buttons=('submit',), use_ajax=True, formid='extraform')
    if not request.user:
        return exc.HTTPFound(request.route_url('login'))
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.owner == request.user.id).one_or_none()
    if not mycarrier:
        return exc.HTTPFound(request.route_url('login'))
    myextra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == mycarrier.id).one_or_none()
    myhooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id).all()

    # Sidebar and menus.
    userdata = usr.populate_user(request)
    sidebar = menu.populate_sidebar(request)
    cdata = carrier_data.populate_view(request, mycarrier.id, request.user)
    tmphooks = []
    for hook in myhooks:
        print(f"Loading calendarevents as {hook.calendarEvents}")
        tmphooks.append({'hook_url': hook.hook_url,
                         'hook_type': hook.hook_type,
                         'enabled': True,
                         'jumpEvents': hook.jumpEvents,
                         'marketEvents': hook.marketEvents,
                         'calendarEvents': hook.calendarEvents,
                         'id': hook.id,
                         'owner_id': hook.owner_id,
                         'carrier_id': hook.carrier_id})

    webhook_settings = webhookform.render({'hooks': tmphooks})
    carrier_settings = carrierform.render(object_as_dict(mycarrier))
    if myextra:
        extra_settings = extraform.render({'carrier_motd': myextra.carrier_motd or ""})
    else:
        extra_settings = extraform.render()

    if 'submit' in request.POST:
        if request.POST['__formid__'] == 'carrierform':
            try:
                controls = request.POST.items()
                appstruct = carrierform.validate(controls)
                mycarrier.fromdict(appstruct)
                request.dbsession.flush()
                request.dbsession.refresh(mycarrier)
                carrier_settings = carrierform.render(object_as_dict(mycarrier))
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier settings updated!'}}
                return {**cdata, **{'sidebar': sidebar, 'userdata': userdata, 'modal': modal_data, 'formadvanced': True,
                                    'carrier_settings': carrier_settings,
                                    'extra_settings': extra_settings,
                                    'carrier_image': myextra.carrier_image if myextra else None,
                                    'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}}
            except ValidationFailure as e:
                carrier_settings = e.render()
                logging.error(f"Carrier Validation failed! {e.error}")
                # modal_data = {'load_fire', {'icon': 'error', 'message': 'Carrier settings invalid!'}}
                return {{**cdata, 'sidebar': sidebar, 'userdata': userdata, 'formadvanced': True,
                         'carrier_settings': carrier_settings,
                         'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                         'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}}
        elif request.POST['__formid__'] == 'extraform':
            cnt = request.POST.items()
            modal_data = {}
            try:
                # lappstruct = extraform.validate(cnt)
                try:
                    cex = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == mycarrier.id).one_or_none()
                    # log.debug(f"Load: {lappstruct}")
                    # Hurr?
                    if request.POST['upload'] != b'':
                        filename = request.storage.save(request.POST['upload'], folder=f'carrier-{mycarrier.id}',
                                                        randomize=True)
                        log.debug(f"Filename pre storage: {filename}")

                        if not cex:
                            log.info(f"Adding new carrier image for {mycarrier.callsign}.")
                            nc = CarrierExtra(cid=mycarrier.id, carrier_image=filename)
                            request.dbsession.add(nc)
                            modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier image uploaded!'}}
                            cex = nc
                        else:
                            try:
                                request.storage.delete(cex.carrier_image)
                                log.info(f"Updated carrier image for {mycarrier.callsign}")
                            except:
                                log.error(f"Failed to delete old image for {mycarrier.callsign}!")
                            cex.carrier_image = filename
                            modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier image updated!'}}
                    if 'carrier_motd' in request.POST and request.POST['carrier_motd'] != '':
                        if not cex:
                            log.info(f"Adding new carrier MOTD.")
                            nc = CarrierExtra(cid=mycarrier.id, carrier_motd=request.POST['carrier_motd'])
                            request.dbsession.add(nc)
                            modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier motto set!'}}
                            cex = nc
                        else:
                            log.info(f"Updated carrier motto for {mycarrier.callsign}")
                            cex.carrier_motd = request.POST['carrier_motd']
                            modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier motto updated!'}}
                    request.dbsession.flush()
                    if not myextra:
                        myextra = request.dbsession.query(CarrierExtra).filter(
                            CarrierExtra.cid == mycarrier.id).one_or_none()
                        extra_settings = extraform.render({'carrier_motd': myextra.carrier_motd or ""})
                    if cex:
                        print(f"CEX is {cex}")
                        request.dbsession.refresh(cex)
                except FileNotAllowed:
                    log.error(
                        f"Attempt to upload invalid file by user {request.user.username} from {request.client_addr}")
                    request.session.flash('Sorry, this file is not allowed.')
                    modal_data = {'load_fire': {'icon': 'error', 'message': 'Sorry, that file type is not allowed.'}}
            except ValidationFailure as e:
                log.debug(f"Failed to validate carrier extra! {e.error}")
                extra_settings = e.render()
                # modal_data = {'load_fire', {'icon': 'error', 'message': 'Something went wrong with that file upload.'}}
                return {'sidebar': sidebar, 'userdata': userdata, 'formadvanced': True,
                        'carrier_settings': carrier_settings,
                        'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                        'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}
            request.dbsession.flush()
            if cex:
                request.dbsession.refresh(cex)
            return {**cdata, **{'sidebar': sidebar, 'userdata': userdata, 'modal': modal_data, 'formadvanced': True,
                                'carrier_settings': carrier_settings,
                                'extra_settings': extra_settings,
                                'carrier_image': myextra.carrier_image if myextra else None,
                                'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}}

        elif request.POST['__formid__'] == 'webhookform':
            controls = request.POST.items()
            try:
                appstruct = webhookform.validate(controls)
                hookids = []
                newids = []
                print(f"Load appstruct {appstruct}")
                for hook in appstruct['hooks']:
                    if 'id' in hook:
                        hookids.append(hook['id'])
                    if 'id' in hook:
                        print(f"Update old hook with {hook['calendarEvents']}")
                        oldhook = request.dbsession.query(Webhook).filter(Webhook.id == hook['id']).one_or_none()
                        oldhook.enabled = hook['enabled']
                        oldhook.hook_url = hook['hook_url']
                        oldhook.hook_type = hook['hook_type']
                        oldhook.jumpEvents = hook['jumpEvents']
                        oldhook.marketEvents = hook['marketEvents']
                        oldhook.calendarEvents = hook['calendarEvents']
                        print("Flush hook")
                        request.dbsession.flush()
                        request.dbsession.refresh(oldhook)
                    else:
                        print(f"Make new hook with {hook['calendarEvents']}")
                        newhook = Webhook(owner_id=request.user.id, carrier_id=mycarrier.id, hook_url=hook['hook_url'],
                                          hook_type=hook['hook_type'], enabled=hook['enabled'],
                                          calendarEvents=hook['calendarEvents'], jumpEvents=hook['jumpEvents'],
                                          marketEvents=hook['marketEvents'])
                        request.dbsession.add(newhook)
                        request.dbsession.flush()
                        request.dbsession.refresh(newhook)
                        newids.append(newhook.id)
                # Check whether any hooks were deleted.
                exthooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id).all()
                for ext in exthooks:
                    # OH MY FUCKING GOD, CHECK THAT THE ROW YOU JUST ADDED ISN'T DELETED IMMEDIATELY AFTER ADDING!!!!!!
                    if ext.id not in hookids:
                        # Hook removed, delete!
                        if ext.id not in newids:
                            request.dbsession.query(Webhook).filter(Webhook.id == ext.id).delete()
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Webhooks updated!'}}
                request.dbsession.flush()
                myhooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id)
                tmphooks = []
                for hook in myhooks:
                    print(f"Refresh form with {hook.calendarEvents}")
                    request.dbsession.refresh(hook)
                    tmphooks.append({'hook_url': hook.hook_url,
                                     'hook_type': hook.hook_type,
                                     'enabled': True,
                                     'jumpEvents': hook.jumpEvents,
                                     'marketEvents': hook.marketEvents,
                                     'calendarEvents': hook.calendarEvents,
                                     'id': hook.id,
                                     'owner_id': hook.owner_id,
                                     'carrier_id': hook.carrier_id})

                webhook_settings = webhookform.render({'hooks': tmphooks})
                return {**cdata, **{'sidebar': sidebar, 'userdata': userdata, 'modal': modal_data, 'formadvanced': True,
                                    'carrier_settings': carrier_settings,
                                    'extra_settings': extra_settings,
                                    'carrier_image': myextra.carrier_image if myextra else None,
                                    'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}}
            except ValidationFailure as e:
                webhook_settings = e.render()
                logging.error(f"Webhooks validation failed! {e.error}")
                # modal_data = {'load_fire', {'icon': 'error', 'message': 'Webhook settings invalid!'}}
                return {**cdata, **{'formadvanced': True, 'carrier_settings': carrier_settings,
                                    'extra_settings': extra_settings,
                                    'carrier_image': myextra.carrier_image if myextra else None,
                                    'webhooks_settings': webhook_settings, 'subview': 'settings', 'view': 'settings'}}

    return {**cdata,
            **{'sidebar': sidebar, 'userdata': userdata, 'formadvanced': True, 'carrier_settings': carrier_settings,
               'webhooks_settings': webhook_settings, 'extra_settings': extra_settings,
               'carrier_image': myextra.carrier_image if myextra else None, 'subview': 'settings', 'view': 'settings'}}
