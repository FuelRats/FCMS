# Carrier settings form target
# Also, images!
import colander
from deform import widget, Form, ValidationFailure
from deform.interfaces import FileUploadTempStore
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed

from ..utils.util import object_as_dict
from ..models import Carrier, CarrierExtra, Calendar, Webhook
import logging

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
imgtemp = FileUploadTempStore()


class CarrierExtraSettings(colander.MappingSchema):
    carrierImage = colander.SchemaNode(colander.String(),
                                       widget=widget.FileUploadWidget(tmpstore=imgtemp),
                                       title='Carrier Image',
                                       description="Choose file to upload")
    carrierMOTD = colander.SchemaNode(colander.String(),
                                      widget=widget.TextInputWidget(),
                                      description="Set your carrier's Motto / MOTD.",
                                      missing=colander.drop)


class WebhookSchema(colander.Schema):
    hook_url = colander.SchemaNode(colander.String(),
                                   widget=widget.TextInputWidget())
    hook_type = colander.SchemaNode(colander.String(),
                                    widget=widget.SelectWidget(values=hooktypes),
                                    validator=colander.OneOf(('discord', 'generic')))
    enabled = colander.SchemaNode(colander.Boolean(),
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
    webhookform.widget.css_class = "col-md"
    extraform = Form(extraschema, buttons=('submit',), use_ajax=True, formid='extraform')

    mycarrier = request.dbsession.query(Carrier).filter(Carrier.owner == request.user.id).one_or_none()
    myextra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == mycarrier.id).one_or_none()
    myhooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id).all()

    tmphooks = []
    for hook in myhooks:
        tmphooks.append({'hook_url': hook.hook_url,
                         'hook_type': hook.hook_type,
                         'enabled': True,
                         'id': hook.id,
                         'owner_id': hook.owner_id,
                         'carrier_id': hook.carrier_id})

    webhook_settings = webhookform.render({'hooks': tmphooks})
    carrier_settings = carrierform.render(object_as_dict(mycarrier))
    extra_settings = extraform.render(object_as_dict(myextra))

    if 'myfile' in request.POST:
        try:
            filename = request.storage.save(request.POST['myfile'], folder=f'carrier-{mycarrier.id}',
                                            randomize=True)
            log.debug(f"Filename pre storage: {filename}")
            cex = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == mycarrier.id).one_or_none()
            if not cex:
                log.info(f"Adding new carrier image for {mycarrier.callsign}.")
                nc = CarrierExtra(cid=mycarrier.id, carrier_image=filename)
                request.dbsession.add(nc)
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier image uploaded!'}}
            else:
                request.storage.delete(cex.carrier_image)
                log.info(f"Updated carrier image for {mycarrier.callsign}")
                cex.carrier_image = filename
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier image updated!'}}

        except FileNotAllowed:
            log.error(f"Attempt to upload invalid file by user {request.user.username} from {request.client_addr}")
            request.session.flash('Sorry, this file is not allowed.')
            modal_data = {'load_fire': {'icon': 'error', 'message': 'Sorry, that file type is not allowed.'}}
        carrier_form = carrierform.render(object_as_dict(mycarrier))
        webhook_form = webhookform.render()
        return {'modal': modal_data, 'formadvanced': True, 'carrier_settings': carrier_form,
                'webhooks_settings': webhook_form, 'carrier_image': myextra.carrier_image,
                'extra_settings': extra_settings}
    if 'submit' in request.POST:
        if request.POST['__formid__'] == 'carrierform':
            try:
                print("Got a carrier form!")
                controls = request.POST.items()
                appstruct = carrierform.validate(controls)
                mycarrier.fromdict(appstruct)
                request.dbsession.flush()
                request.dbsession.refresh(mycarrier)
                carrier_settings = carrierform.render(object_as_dict(mycarrier))
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Carrier settings updated!'}}
                return {'modal': modal_data, 'formadvanced': True, 'carrier_settings': carrier_settings,
                        'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                        'webhooks_settings': webhook_settings}
            except ValidationFailure as e:
                carrier_settings = e.render()
                logging.error(f"Validation failed!")
                modal_data = {'load_fire', {'icon': 'error', 'message': 'Carrier settings invalid!'}}
                return {'modal': modal_data, 'formadvanced': True, 'carrier_settings': carrier_settings,
                        'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                        'webhooks_settings': webhook_settings}

        elif request.POST['__formid__'] == 'webhookform':
            print("Got a webhooks form!")
            controls = request.POST.items()
            try:
                appstruct = webhookform.validate(controls)
                print(f"appstruct: {appstruct}")
                hookids=[]
                newids=[]
                for hook in appstruct['hooks']:
                    print(f"Hook: {hook['hook_url']}")
                    if 'id' in hook:
                        print("Hook has ID.")
                        print(hook)
                        hookids.append(hook['id'])
                    else:
                        print("No hook id?")
                    if 'id' in hook:
                        oldhook = request.dbsession.query(Webhook).filter(Webhook.id == hook['id'])
                        oldhook.enabled = hook['enabled']
                        oldhook.hook_url = hook['hook_url']
                        oldhook.hook_type = hook['hook_type']
                    else:
                        newhook = Webhook(owner_id=request.user.id, carrier_id=mycarrier.id, hook_url=hook['hook_url'],
                                          hook_type=hook['hook_type'], enabled=hook['enabled'])
                        request.dbsession.add(newhook)
                        request.dbsession.flush()
                        request.dbsession.refresh(newhook)
                        newids.append(newhook.id)
                #Check whether any hooks were deleted.
                exthooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id).all()
                for ext in exthooks:
                    # OH MY FUCKING GOD, CHECK THAT THE ROW YOU JUST ADDED ISN'T DELETED IMMEDIATELY AFTER ADDING!!!!!!
                    if ext.id not in hookids:
                        # Hook removed, delete!
                        if ext.id not in newids:
                            request.dbsession.query(Webhook).filter(Webhook.id==ext.id).delete()
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Webhooks updated!'}}
                request.dbsession.flush()
                myhooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == mycarrier.id)
                tmphooks = []
                for hook in myhooks:
                    request.dbsession.refresh(hook)
                    print(f"Proc hook: {hook}")
                    tmphooks.append({'hook_url': hook.hook_url,
                                     'hook_type': hook.hook_type,
                                     'enabled': True,
                                     'id': hook.id,
                                     'owner_id': hook.owner_id,
                                     'carrier_id': hook.carrier_id})

                webhook_settings = webhookform.render({'hooks': tmphooks})
                return {'modal': modal_data, 'formadvanced': True, 'carrier_settings': carrier_settings,
                            'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                            'webhooks_settings': webhook_settings}
            except ValidationFailure as e:
                webhook_settings = e.render()
                logging.error(f"Webhooks validation failed!")
                print(e.error)
                # modal_data = {'load_fire', {'icon': 'error', 'message': 'Webhook settings invalid!'}}
                return {'formadvanced': True, 'carrier_settings': carrier_settings,
                        'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image,
                        'webhooks_settings': webhook_settings}

    return {'formadvanced': True, 'carrier_settings': carrier_settings, 'webhooks_settings': webhook_settings,
            'extra_settings': extra_settings, 'carrier_image': myextra.carrier_image}
