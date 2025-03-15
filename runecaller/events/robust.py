"""Module implementing error-catching version of send (sendRobust)"""

import asyncio
from typing import Any, Callable, List, Tuple, Union
from runecaller.events.dispatcher import liveReceivers, getAllReceivers
from runecaller.events.robustapply import robustApply

async def sendRobust(
    signal: Any = Any,
    sender: Any = None,
    *arguments: Any, **named: Any
) -> List[Tuple[Callable, Union[Any, Exception]]]:
    """Send signal from sender to all connected receivers catching errors

    signal -- (hashable) signal value, see connect for details

    sender -- the sender of the signal

        if Any, only receivers registered for Any will receive
        the message.

        if None, only receivers registered to receive
        messages from None or Any will receive the message

        Otherwise can be any python object (normally one
        registered with a connect if you actually want
        something to occur).

    arguments -- positional arguments which will be passed to *all* receivers. Note that this may raise TypeErrors
        if the receivers do not allow the particular arguments.
        Note also that arguments are applied before named arguments, so they should be used with care.

    named -- named arguments which will be filtered according to the parameters of the receivers to only provide those
        acceptable to the receiver.

    Return a list of tuple pairs [(receiver, response), ... ]

    if any receiver raises an error (specifically any subclass of Exception),
    the error instance is returned as the result for that receiver.
    """
    responses = []
    for receiver in liveReceivers(getAllReceivers(sender, signal)):
        try:
            if asyncio.iscoroutinefunction(receiver):
                response = await robustApply(
                    receiver,
                    signal=signal,
                    sender=sender,
                    *arguments,
                    **named
                )
            else:
                response = robustApply(
                    receiver,
                    signal=signal,
                    sender=sender,
                    *arguments,
                    **named
                )
        except Exception as err:
            responses.append((receiver, err))
        else:
            responses.append((receiver, response))
    return responses