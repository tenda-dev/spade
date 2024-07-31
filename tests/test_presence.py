from unittest.mock import Mock

import pytest
import slixmpp.roster

from spade.presence import ContactNotFound, PresenceShow, PresenceType
from .factories import MockedPresenceAgentFactory

from slixmpp.stanza import Presence
from slixmpp import JID

async def test_get_state_not_available():
    agent = MockedPresenceAgentFactory(available=False, show=PresenceShow.NONE)

    await agent.start(auto_register=False)

    assert agent.presence.current_available is None
    assert agent.presence.current_status is None
    assert agent.presence.current_show is PresenceShow.NONE


async def test_get_state_available():
    agent = MockedPresenceAgentFactory(available=True)

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.current_available


async def test_set_available():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_available()

    assert agent.presence.is_available()


async def test_set_available_with_show():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_available(show=PresenceShow.CHAT)

    assert agent.presence.is_available()
    assert agent.presence.current_show == PresenceShow.CHAT


async def test_set_unavailable():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_unavailable()

    assert not agent.presence.is_available()


async def test_get_state_show():
    agent = MockedPresenceAgentFactory(available=True, show=PresenceShow.AWAY)

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.current_show == PresenceShow.AWAY


async def test_get_status_empty():
    agent = MockedPresenceAgentFactory(status={})

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.status == {}


async def test_get_status_string():
    agent = MockedPresenceAgentFactory(status="Working")

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.status == {None: "Working"}


async def test_get_status_dict():
    agent = MockedPresenceAgentFactory(status={"en": "Working"})

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.status == {"en": "Working"}


async def test_get_priority_default():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.priority == 0


async def test_get_priority():
    agent = MockedPresenceAgentFactory(priority=10)

    await agent.start(auto_register=False)

    agent.mock_presence()

    assert agent.presence.priority == 10


async def test_set_presence_available():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_available()

    assert agent.presence.is_available()


async def test_set_presence_unavailable():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_unavailable()

    assert not agent.presence.is_available()


async def test_set_presence_status():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_presence(status="Lunch")

    assert agent.presence.status == {None: "Lunch"}


async def test_set_presence_status_dict():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_presence(status={"en": "Lunch"})

    assert agent.presence.status == {"en": "Lunch"}


async def test_set_presence_priority():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_presence(priority=5)

    assert agent.presence.priority == 5


async def test_set_presence():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.set_available()
    agent.presence.set_presence(show=PresenceShow.NONE, status="Lunch", priority=2)

    assert agent.presence.is_available()
    assert agent.presence.current_show == PresenceShow.NONE
    assert agent.presence.status == {None: "Lunch"}
    assert agent.presence.priority == 2


async def test_get_contacts_empty():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    assert agent.presence.get_contacts() == {}


async def test_get_contacts(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My Friend"
    )

    contacts = agent.presence.get_contacts()

    bare_jid = jid.bare
    assert bare_jid in contacts
    assert type(contacts[bare_jid]) == slixmpp.roster.RosterItem
    assert contacts[bare_jid]["name"] == "My Friend"
    assert contacts[bare_jid]["subscription"] == "none"
    assert contacts[bare_jid]['pending_out'] is False
    assert not contacts[bare_jid]['groups']


async def test_get_contacts_with_presence(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My Available Friend"
    )

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.SUBSCRIBE.value

    agent.client.event("presence_subscribe", stanza)

    contacts = agent.presence.get_contacts()

    bare_jid = jid.bare
    assert bare_jid in contacts
    assert contacts[bare_jid]["name"] == "My Available Friend"


async def test_get_contacts_with_presence_on_and_off(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My Friend"
    )

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.AVAILABLE.value

    agent.client.event("presence_available", stanza)

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = 'unavailable'

    agent.client.event("presence_unavailable", stanza)

    contacts = agent.presence.get_contacts()

    bare_jid = jid.bare
    assert bare_jid in contacts
    assert contacts[bare_jid]["name"] == "My Friend"
    assert contacts[bare_jid]["presence"].get_type() == 'unavailable'


async def test_get_contacts_with_presence_unavailable(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My UnAvailable Friend"
    )

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = 'unavailable'

    agent.client.event("presence_unavailable", stanza)

    contacts = agent.presence.get_contacts()

    bare_jid = jid.bare
    assert bare_jid in contacts
    assert contacts[bare_jid]["name"] == "My UnAvailable Friend"
    assert contacts[bare_jid]["presence"].get_type() == 'unavailable'


async def test_get_contact(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My Friend"
    )
    agent.client.client_roster[jid.bare]['whitelisted'] = True
    agent.client.client_roster[jid.bare].save()

    contact = agent.presence.get_contact(jid)

    assert type(contact) == slixmpp.roster.RosterItem
    assert contact["name"] == "My Friend"
    assert contact["subscription"] == "none"
    assert contact["whitelisted"] == True
    assert contact['pending_out'] is False
    assert len(contact['groups']) == 0


async def test_get_invalid_jid_contact():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    with pytest.raises(ContactNotFound):
        agent.presence.get_contact(JID("invalid@contact"))


async def test_get_invalid_str_contact():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    with pytest.raises(AttributeError):
        agent.presence.get_contact("invalid@contact")


async def test_subscribe(jid):
    peer_jid = str(jid)
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.send_presence_subscription = Mock()
    agent.presence.subscribe(peer_jid)

    assert agent.client.send_presence_subscription.mock_calls
    arg = agent.client.send_presence_subscription.call_args[1]

    assert arg['pto'] == jid.bare
    assert arg['ptype'] == PresenceType.SUBSCRIBE.value


async def test_unsubscribe(jid):
    peer_jid = str(jid)
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.send_presence_subscription = Mock()
    agent.presence.unsubscribe(peer_jid)

    assert agent.client.send_presence_subscription.mock_calls
    arg = agent.client.send_presence_subscription.call_args[1]

    assert arg['pto'] == jid.bare
    assert arg['ptype'] == PresenceType.UNSUBSCRIBE.value


async def test_approve(jid):
    peer_jid = str(jid)
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.send_presence_subscription = Mock()
    agent.presence.approve(peer_jid)

    assert agent.client.send_presence_subscription.mock_calls
    arg = agent.client.send_presence_subscription.call_args[1]

    assert arg['pto'] == jid.bare
    assert arg['ptype'] == PresenceType.SUBSCRIBED.value


async def test_on_available(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_available = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.AVAILABLE.value

    agent.client.event("presence_available", stanza)

    assert agent.presence.on_available.mock_calls

    jid_arg = agent.presence.on_available.call_args[0][0]
    stanza_arg = agent.presence.on_available.call_args[0][1]

    assert jid_arg == str(jid)
    assert stanza_arg['type'] == PresenceType.AVAILABLE.value


async def test_on_unavailable(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_unavailable = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = 'unavailable'

    agent.client.event("presence_unavailable", stanza)

    assert agent.presence.on_unavailable.mock_calls

    jid_arg = agent.presence.on_unavailable.call_args[0][0]
    stanza_arg = agent.presence.on_unavailable.call_args[0][1]

    assert jid_arg == str(jid)
    assert stanza_arg['type'] == 'unavailable'


async def test_on_subscribe(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_subscribe = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.SUBSCRIBE.value

    agent.client.event("presence_subscribe", stanza)

    assert agent.presence.on_subscribe.mock_calls

    jid_arg = agent.presence.on_subscribe.call_args[0][0]

    assert jid_arg == str(jid)


async def test_on_subscribe_approve_all(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.approve_all = True
    agent.client.send_presence_subscription = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.SUBSCRIBE.value

    agent.client.event("presence_subscribe", stanza)

    assert agent.client.send_presence_subscription.mock_calls
    arg = agent.client.send_presence_subscription.call_args[1]

    assert arg['pto'] == jid.bare
    assert arg['ptype'] == PresenceType.SUBSCRIBED.value


async def test_on_subscribed(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_subscribed = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.SUBSCRIBED.value

    agent.client.event("presence_subscribed", stanza)

    jid_arg = agent.presence.on_subscribed.call_args[0][0]

    assert jid_arg == str(jid)


async def test_on_unsubscribe(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_unsubscribe = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.UNSUBSCRIBE.value

    agent.client.event("presence_unsubscribe", stanza)

    jid_arg = agent.presence.on_unsubscribe.call_args[0][0]

    assert jid_arg == str(jid)


async def test_on_unsubscribe_approve_all(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.approve_all = True
    agent.client.send_presence_subscription = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza['type'] = PresenceType.UNSUBSCRIBED.value

    agent.client.event("presence_unsubscribe", stanza)

    assert agent.client.send_presence_subscription.mock_calls
    arg = agent.client.send_presence_subscription.call_args[1]

    assert arg['pto'] == jid.bare
    assert arg['ptype'] == PresenceType.UNSUBSCRIBED.value


async def test_on_unsubscribed(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.presence.on_unsubscribed = Mock()

    stanza = Presence()
    stanza['from'] = jid
    stanza.set_type(PresenceType.UNSUBSCRIBED.value)

    agent.client.event("presence_unsubscribed", stanza)

    jid_arg = agent.presence.on_unsubscribed.call_args[0][0]

    assert jid_arg == str(jid)


async def test_on_changed(jid):
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    agent.client.update_roster(
        jid=jid,
        name="My Friend"
    )

    stanza = Presence()
    stanza['from'] = jid
    stanza.set_type(PresenceType.AVAILABLE.value)
    stanza.set_show(PresenceShow.CHAT.value)

    agent.client.event("presence_available", stanza)

    contact = agent.presence.get_contact(jid)
    assert contact["name"] == "My Friend"
    assert contact["presence"].get_type() == PresenceShow.CHAT.value

    stanza = Presence()
    stanza['from'] = jid
    stanza.set_type(PresenceType.AVAILABLE.value)
    stanza.set_show(PresenceShow.AWAY.value)

    agent.client.event("presence_available", stanza)

    contact = agent.presence.get_contact(jid)

    assert contact["name"] == "My Friend"
    assert contact["presence"].get_type() == PresenceShow.AWAY.value


async def test_ignore_self_presence():
    agent = MockedPresenceAgentFactory()

    await agent.start(auto_register=False)

    jid = agent.jid

    stanza = Presence()
    stanza['from'] = jid
    stanza.set_type(PresenceType.AVAILABLE.value)
    stanza.set_show(PresenceShow.CHAT.value)

    agent.client.event("presence_available", stanza)

    with pytest.raises(ContactNotFound):
        agent.presence.get_contact(jid)

    assert len(agent.presence.get_contacts()) == 0
