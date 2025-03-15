"""Providing the primary API and the core logic for the event system.

Module attributes of note:

    Any -- Singleton used to signal either "Any Sender" or "Any Signal".  See documentation of the _Any class.
    Anonymous -- Singleton used to signal "Anonymous Sender".  See documentation of the _Anonymous class.

Internal attributes:
    WEAKREF_TYPES -- tuple of types/classes which represent
        weak references to receivers, and thus must be de-referenced on retrieval to retrieve the callable object
    connections -- { senderkey (id) : { signal : [receivers...]}}
    senders -- { senderkey (id) : weakref(sender) }
        used for cleaning up sender references on sender deletion
    sendersBack -- { receiverkey (id) : [senderkey (id)...] }
        used for cleaning up receiver references on receiver deletion, (considerably speeds up the cleanup process
        vs. the original code.)
"""

import weakref
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from runecaller.events import robustapply

connections: Dict[int, Dict[Any, List[Callable]]] = {}
sendersBack: Dict[int, set] = {}
senders: Dict[int, weakref.ReferenceType] = {}

def getReceivers(sender: Any, signal: Any) -> List[Callable]:
    try:
        return connections[id(sender)][signal]
    except KeyError:
        return []

def liveReceivers(receivers: List[Union[Callable, weakref.ReferenceType]]) -> Callable:
    for receiver in receivers:
        if isinstance(receiver, weakref.ReferenceType):
            receiver = receiver()
            if receiver is not None:
                yield receiver
        else:
            yield receiver

def getAllReceivers(sender: Any = Any, signal: Any = Any) -> Callable:
    receivers = {}
    for set in (
        getReceivers(sender, signal),
        getReceivers(sender, Any),
        getReceivers(Any, signal),
        getReceivers(Any, Any),
    ):
        for receiver in set:
            if receiver:
                try:
                    if receiver not in receivers:
                        receivers[receiver] = 1
                        yield receiver
                except TypeError:
                    pass

def send(signal: Any = Any, sender: Any = None, *arguments, **named) -> List[Tuple[Callable, Any]]:
    responses = []
    for receiver in liveReceivers(getAllReceivers(sender, signal)):
        response = robustapply.robustApply(
            receiver,
            signal=signal,
            sender=sender,
            *arguments,
            **named
        )
        responses.append((receiver, response))
    return responses

def sendExact(signal: Any = Any, sender: Any = None, *arguments, **named) -> List[Tuple[Callable, Any]]:
    responses = []
    for receiver in liveReceivers(getReceivers(sender, signal)):
        response = robustapply.robustApply(
            receiver,
            signal=signal,
            sender=sender,
            *arguments,
            **named
        )
        responses.append((receiver, response))
    return responses

def _removeReceiver(receiver: Callable) -> bool:
    if not sendersBack:
        return False
    backKey = id(receiver)
    try:
        backSet = sendersBack.pop(backKey)
    except KeyError:
        return False
    else:
        for senderkey in backSet:
            try:
                signals = list(connections[senderkey].keys())
            except KeyError:
                pass
            else:
                for signal in signals:
                    try:
                        receivers = connections[senderkey][signal]
                    except KeyError:
                        pass
                    else:
                        try:
                            receivers.remove(receiver)
                        except Exception:
                            pass
                    _cleanupConnections(senderkey, signal)
        return True

def _cleanupConnections(senderkey: int, signal: Any) -> None:
    try:
        receivers = connections[senderkey][signal]
    except KeyError:
        pass
    else:
        if not receivers:
            try:
                signals = connections[senderkey]
            except KeyError:
                pass
            else:
                del signals[signal]
                if not signals:
                    _removeSender(senderkey)

def _removeSender(senderkey: int) -> None:
    _removeBackrefs(senderkey)
    try:
        del connections[senderkey]
    except KeyError:
        pass
    try:
        del senders[senderkey]
    except KeyError:
        pass

def _removeBackrefs(senderkey: int) -> None:
    try:
        signals = connections[senderkey]
    except KeyError:
        signals = None
    else:
        items = signals.items()
        def allReceivers():
            for signal, set in items:
                for item in set:
                    yield item
        for receiver in allReceivers():
            _killBackref(receiver, senderkey)

def _removeOldBackRefs(senderkey: int, signal: Any, receiver: Callable, receivers: List[Callable]) -> bool:
    try:
        index = receivers.index(receiver)
    except ValueError:
        return False
    else:
        oldReceiver = receivers[index]
        del receivers[index]
        found = 0
        signals = connections.get(signal)
        if signals is not None:
            for sig, recs in connections.get(signal, {}).items():
                if sig != signal:
                    for rec in recs:
                        if rec is oldReceiver:
                            found = 1
                            break
        if not found:
            _killBackref(oldReceiver, senderkey)
            return True
        return False

def _killBackref(receiver: Callable, senderkey: int) -> bool:
    receiverkey = id(receiver)
    set = sendersBack.get(receiverkey, set())
    while senderkey in set:
        try:
            set.remove(senderkey)
        except KeyError:
            break
    if not set:
        try:
            del sendersBack[receiverkey]
        except KeyError:
            pass
    return True