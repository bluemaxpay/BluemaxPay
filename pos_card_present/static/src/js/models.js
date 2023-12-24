/** @odoo-module */
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentCardPresent } from "@pos_card_present/js/payment_card_present";

register_payment_method('card_present', PaymentCardPresent);