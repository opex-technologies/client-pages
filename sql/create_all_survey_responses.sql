
CREATE OR REPLACE VIEW `opex-data-lake-k23k4y98m.scoring.all_survey_responses` AS

    SELECT 
        COALESCE(CAST(timestamp AS STRING), CAST(inserted_at AS STRING)) as timestamp,
        COALESCE(source, 'network_security_survey') as source,
        IFNULL(contact_name, '') as contact_name,
        IFNULL(contact_email, '') as contact_email,
        IFNULL(contact_company, '') as contact_company,
        IFNULL(contact_phone, '') as contact_phone,
        IFNULL(company_name, '') as company_name,
        'network_security_survey' as survey_type,
        question,
        CAST(answer AS STRING) as answer,
        inserted_at
    FROM `opex-data-lake-k23k4y98m.opex_dev.network_security_survey`
    UNPIVOT(answer FOR question IN (`year_founded`, `headquarters`, `parent_company`, `year_sd_wan_launched`, `year_sase_platform_launched`, `do_you_offer_circuit_procurement`, `do_you_hold_direct_contracts_with_the_circuit_providers__or_do_you_leverage_an_aggregator_`, `do_you_offer_circuit_management`, `do_you_actively_monitor_and_proactively_open_tickets_for_circuit_issues`, `is_onsite_hardware_replacement_included`, `what_is_your_sla_for_onsite_replacement`, `what_is_your_sla_for_p1_incident_response`, `do_you_provide_an_uptime_sla_if_both_hardware_and_circuits_are_procured_through_you__what_is_the_sla_`, `do_you_provide_client_access_to_the_sd_wan_portal__co_management_`, `can_you_shift_traffic_mid_session`, `do_you_support_throughput_monitoring`, `do_you_support_full_mesh__if_so__what_is_the_maximum_number_of_sites_in_a_full_mesh_`, `how_do_you_connect_into_aws_and_azure_`, `how_do_you_license_ha_`, `do_you_have_a_middle_mile_network_`, `do_you_support_packet_duplication`, `do_you_support_forward_error_correction`, `what_is_your_historical_reporting_retention_period`, `do_you_provide_real_time_traffic_visibility_and_analytics`, `what_is_your_speed_to_failover_between_circuits`, `can_you_handle_inbound_traffic_for_hosted_systems`, `do_you_offer_client_specific_static_ips`, `do_you_have_unified_ruleset_across_all_locations_pops`, `do_you_provide_content_filtering`, `do_you_tie_back_to_endpoint_context`, `do_you_provide_anti_malware__signature_based_`, `do_you_provide_next_gen_anti_malware__ml_based_`, `do_you_provide_ips_ids`, `do_you_provide_casb`, `do_you_provide_dlp`, `can_you_export_logs_in_near_real_time_to_mdr_provider___splunk`, `do_you_support_multiple_wan_segments__multiple_vrfs_`, `is_remote_access_always_on`, `do_all_cloud_firewall_services_apply_to_remote_access_clients`, `do_you_auto_select_nearest_pop`, `how_many_pops_do_you_have`, `do_you_have_access_to_middle_mile_network_for_optimal_egress`, `what_is_your_maximum_throughput`))
UNION ALL

    SELECT 
        COALESCE(CAST(timestamp AS STRING), CAST(inserted_at AS STRING)) as timestamp,
        COALESCE(source, 'test_form') as source,
        '' as contact_name,
        '' as contact_email,
        '' as contact_company,
        '' as contact_phone,
        '' as company_name,
        'test_form' as survey_type,
        question,
        CAST(answer AS STRING) as answer,
        inserted_at
    FROM `opex-data-lake-k23k4y98m.opex_dev.test_form`
    UNPIVOT(answer FOR question IN (`name`, `email`, `company`, `phone`, `subject`, `message`, `priority`, `contactMethod`))
