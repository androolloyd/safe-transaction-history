import logging
from random import randint

from django.test import TestCase

from ..ethereum_service import EthereumServiceProvider
from ..models import MultisigConfirmation, MultisigTransaction
from ..tasks import check_approve_transaction
from .factories import (MultisigTransactionConfirmationFactory,
                        MultisigTransactionFactory)
from .safe_test_case import TestCaseWithSafeContractMixin

logger = logging.getLogger(__name__)


class TestTasks(TestCase, TestCaseWithSafeContractMixin):
    WITHDRAW_AMOUNT = 50000000000000000

    @classmethod
    def setUpTestData(cls):
        cls.ethereum_service = EthereumServiceProvider()
        cls.w3 = cls.ethereum_service.w3
        cls.prepare_safe_tests()

    def test_task_flow(self):
        safe_address, safe_instance, owners, funder, fund_amount, _ = self.deploy_safe()
        safe_nonce = randint(0, 10)

        multisig_transaction = MultisigTransactionFactory(safe=safe_address, to=owners[0], value=self.WITHDRAW_AMOUNT,
                                                          operation=self.CALL_OPERATION, nonce=safe_nonce)

        # Send Tx signed by owner 0
        tx_hash_owner0 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[0]
        })

        internal_tx_hash_owner0 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[0]
        })

        is_approved = safe_instance.functions.isApproved(internal_tx_hash_owner0.hex(), owners[0]).call()
        self.assertTrue(is_approved)

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       owner=owners[0],
                                                                       contract_transaction_hash=internal_tx_hash_owner0.hex())

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner0.hex(), tx_hash_owner0.hex(), owners[0],
                                  retry=False)

        # Send Tx signed by owner 1
        tx_hash_owner1 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        internal_tx_hash_owner1 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[1]
        })

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       block_number=self.w3.eth.blockNumber,
                                                                       owner=owners[1],
                                                                       transaction_hash=tx_hash_owner1.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner1.hex())

        # Execute transaction
        tx_exec_hash_owner1 = safe_instance.functions.execTransactionIfApproved(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner1.hex(), tx_hash_owner1.hex(), owners[1],
                                  retry=False)

        multisig_transaction_check = MultisigTransaction.objects.get(safe=safe_address, to=owners[0],
                                                                     value=self.WITHDRAW_AMOUNT, nonce=safe_nonce)
        self.assertTrue(multisig_transaction_check.status)

    def test_task_flow_bis(self):
        safe_address, safe_instance, owners, funder, fund_amount, _ = self.deploy_safe()
        safe_nonce = randint(0, 10)

        multisig_transaction = MultisigTransactionFactory(safe=safe_address, to=owners[0], value=self.WITHDRAW_AMOUNT,
                                                          operation=self.CALL_OPERATION, nonce=safe_nonce)

        # Send Tx signed by owner 0
        tx_hash_owner0 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[0]
        })

        internal_tx_hash_owner0 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[0]
        })


        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner0.hex())

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner0.hex(), tx_hash_owner0.hex(), owners[0],
                                  retry=False)

        multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex())
        self.assertTrue(multisig_confirmation_check.status)

        # Send Tx signed by owner 1
        tx_hash_owner1 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        internal_tx_hash_owner1 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[1]
        })

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       block_number=self.w3.eth.blockNumber,
                                                                       owner=owners[1],
                                                                       transaction_hash=tx_hash_owner1.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner1.hex())

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner1.hex(), tx_hash_owner1.hex(), owners[1],
                                  retry=False)

        multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                       owner=owners[1],
                                                                       transaction_hash=tx_hash_owner1.hex())
        self.assertTrue(multisig_confirmation_check.status)

        # send other approval from a third user
        tx_hash_owner2 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[2]
        })

        internal_tx_hash_owner2 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[2]
        })

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       block_number=self.w3.eth.blockNumber,
                                                                       owner=owners[2],
                                                                       transaction_hash=tx_hash_owner2.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner2.hex())

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner2.hex(), tx_hash_owner2.hex(), owners[2],
                                  retry=False)

        # Execute transaction after owner 1 sent approval
        tx_exec_hash_owner1 = safe_instance.functions.execTransactionIfApproved(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        check_approve_transaction(safe_address, internal_tx_hash_owner2.hex(), tx_hash_owner2.hex(), owners[2],
                                  retry=False)

        multisig_transaction_check = MultisigTransaction.objects.get(safe=safe_address, to=owners[0],
                                                                     value=self.WITHDRAW_AMOUNT, nonce=safe_nonce)
        self.assertTrue(multisig_transaction_check.status)

    def test_block_number_different_confirmation_ok(self):
        safe_address, safe_instance, owners, funder, fund_amount, _ = self.deploy_safe()
        safe_nonce = randint(0, 10)

        multisig_transaction = MultisigTransactionFactory(safe=safe_address, to=owners[0], value=self.WITHDRAW_AMOUNT,
                                                          operation=self.CALL_OPERATION, nonce=safe_nonce)

        # Send Tx signed by owner 0
        tx_hash_owner0 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[0]
        })

        internal_tx_hash_owner0 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[0]
        })

        is_approved = safe_instance.functions.isApproved(internal_tx_hash_owner0.hex(), owners[0]).call()
        self.assertTrue(is_approved)

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner0.hex())

        multisig_confirmation.block_number = multisig_confirmation.block_number + self.w3.eth.blockNumber
        multisig_confirmation.save()

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner0.hex(), tx_hash_owner0.hex(), owners[0],
                                  retry=False)

        multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex())
        self.assertTrue(multisig_confirmation_check.status)

    def test_confirmation_ko(self):
        safe_address, safe_instance, owners, funder, fund_amount, _ = self.deploy_safe()
        safe_nonce = randint(0, 10)
        not_owners = self.w3.eth.accounts[3:-1]

        multisig_transaction = MultisigTransactionFactory(safe=safe_address, to=owners[0], value=self.WITHDRAW_AMOUNT,
                                                          operation=self.CALL_OPERATION, nonce=safe_nonce)

        # Send Tx signed by owner 0
        tx_hash_owner0 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[0]
        })

        internal_tx_hash_owner0 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[0]
        })

        # Simulate reorg, transaction not existing on the blockchain
        transaction_hash = '0xb7b9b497b5138507b767e2433df124a6ffc1cb0812d63e3e38bb6b3667a53149'

        is_approved = safe_instance.functions.isApproved(transaction_hash, owners[0]).call()
        self.assertFalse(is_approved)

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       owner=owners[0],
                                                                       transaction_hash=transaction_hash,
                                                                       contract_transaction_hash=transaction_hash)

        # Execute task
        check_approve_transaction(safe_address, transaction_hash, transaction_hash, owners[0], retry=False)

        with self.assertRaises(MultisigConfirmation.DoesNotExist):
            multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                           owner=owners[0],
                                                                           transaction_hash=transaction_hash)

    def test_block_number_different(self):
        safe_address, safe_instance, owners, funder, fund_amount, _ = self.deploy_safe()
        safe_nonce = randint(0, 10)

        multisig_transaction = MultisigTransactionFactory(safe=safe_address, to=owners[0], value=self.WITHDRAW_AMOUNT,
                                                          operation=self.CALL_OPERATION, nonce=safe_nonce)

        # Send Tx signed by owner 0
        tx_hash_owner0 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[0]
        })

        internal_tx_hash_owner0 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[0]
        })

        is_approved = safe_instance.functions.isApproved(internal_tx_hash_owner0.hex(), owners[0]).call()
        self.assertTrue(is_approved)

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner0.hex())

        multisig_confirmation.block_number = self.w3.eth.blockNumber - 1
        multisig_confirmation.save()

        # Execute task
        check_approve_transaction(safe_address, internal_tx_hash_owner0.hex(), tx_hash_owner0.hex(), owners[0],
                                  retry=False)

        multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                       owner=owners[0],
                                                                       transaction_hash=tx_hash_owner0.hex())
        self.assertTrue(multisig_confirmation_check.status)

        # Send Tx signed by owner 1
        tx_hash_owner1 = safe_instance.functions.approveTransactionWithParameters(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        internal_tx_hash_owner1 = safe_instance.functions.getTransactionHash(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).call({
            'from': owners[1]
        })

        multisig_confirmation = MultisigTransactionConfirmationFactory(multisig_transaction=multisig_transaction,
                                                                       block_number=self.w3.eth.blockNumber,
                                                                       owner=owners[1],
                                                                       transaction_hash=tx_hash_owner1.hex(),
                                                                       contract_transaction_hash=internal_tx_hash_owner1.hex())

        multisig_confirmation.block_number = self.w3.eth.blockNumber - 1
        multisig_confirmation.save()

        check_approve_transaction(safe_address, internal_tx_hash_owner1.hex(), tx_hash_owner1.hex(), owners[1],
                                  retry=False)

        multisig_confirmation_check = MultisigConfirmation.objects.get(multisig_transaction__safe=safe_address,
                                                                       owner=owners[1],
                                                                       transaction_hash=tx_hash_owner1.hex())
        self.assertTrue(multisig_confirmation_check.status)

        # Execute transaction after owner 1 sent approval
        tx_exec_hash_owner1 = safe_instance.functions.execTransactionIfApproved(
            owners[0], self.WITHDRAW_AMOUNT, b'', self.CALL_OPERATION, safe_nonce
        ).transact({
            'from': owners[1]
        })

        check_approve_transaction(safe_address, internal_tx_hash_owner1.hex(), tx_hash_owner1.hex(), owners[1],
                                  retry=False)

        multisig_transaction_check = MultisigTransaction.objects.get(safe=safe_address, to=owners[0],
                                                                     value=self.WITHDRAW_AMOUNT, nonce=safe_nonce)
        self.assertTrue(multisig_transaction_check.status)
