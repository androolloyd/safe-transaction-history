from django.db import models
from model_utils.models import TimeStampedModel

from django_eth.models import EthereumAddressField, Sha3HashField, Uint256Field


class MultisigTransaction(TimeStampedModel):
    safe = EthereumAddressField()
    to = EthereumAddressField()
    value = Uint256Field()
    data = models.BinaryField(null=True)
    operation = models.PositiveSmallIntegerField()
    nonce = Uint256Field()
    status = models.BooleanField(default=False)  # True if transaction executed, 0 otherwise
    # Defines when a multisig transaction gets executed (confirmations included)
    execution_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        executed = 'Executed' if self.status else 'Pending'
        return '{} - {}'.format(self.safe, executed)


class MultisigConfirmation(TimeStampedModel):
    owner = EthereumAddressField()
    contract_transaction_hash = Sha3HashField(null=False, blank=False)
    transaction_hash = Sha3HashField(null=False, blank=False)
    type = models.CharField(max_length=20, null=False, blank=False)
    block_number = models.BigIntegerField()
    block_date_time = models.DateTimeField()
    status = models.BooleanField(default=False)  # True if transaction mined and executed successfully, 0 otherwise
    multisig_transaction = models.ForeignKey(MultisigTransaction,
                                             on_delete=models.CASCADE,
                                             related_name="confirmations")

    def __str__(self):
        mined = 'Mined and executed' if self.status else 'Pending'
        return '{} - {}'.format(self.safe, mined)
