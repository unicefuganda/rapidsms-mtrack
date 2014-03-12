-- when xform_submission is inserted, deleted or updated
CREATE OR REPLACE FUNCTION update_facility_extras() RETURNS TRIGGER AS $update_facility_extras$
    DECLARE
    f INTEGER;
    hp INTEGER;
    extras_id INTEGER;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            SELECT contact_id INTO hp FROM rapidsms_connection WHERE id = OLD.connection_id;
            -- update total reports for health providers
            UPDATE healthmodels_healthproviderextras SET total_reports = total_reports - 1
                WHERE health_provider_id = hp;
            IF OLD.has_errors = FALSE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports - 1
                    WHERE health_facility_id = f;
                END IF;
            END IF;
            RETURN OLD;
        END IF;
        SELECT contact_id INTO hp FROM rapidsms_connection WHERE id = NEW.connection_id;
        IF hp IS NULL THEN
            RETURN NULL;
        END IF;
        IF TG_OP = 'INSERT'  THEN -- insert or update
            -- update total reports for health providers
            UPDATE healthmodels_healthproviderextras SET total_reports = total_reports + 1
                WHERE health_provider_id = hp;
            IF NEW.has_errors = FALSE AND NEW.connection_id IS NOT NULL THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports + 1
                    WHERE health_facility_id = f;
                END IF;
            END IF;
            RETURN NEW;
        ELSIF TG_OP = 'UPDATE' THEN
            IF NEW.has_errors = OLD.has_errors THEN
                -- this part(if clause) caters for a report which has no errors and is not being edited(i.e just created)
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    SELECT submission_id INTO extras_id FROM rapidsms_xforms_xformsubmissionextras WHERE submission_id = NEW.id;
                    IF extras_id IS NULL THEN
                        INSERT INTO rapidsms_xforms_xformsubmissionextras (submission_id, facility_id, cdate, reporter_id)
                        VALUES(NEW.id, f, NOW(), hp);
                    END IF;
                END IF;
                RETURN NEW;
            END IF;
            IF NEW.has_errors = FALSE AND OLD.has_errors = TRUE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports + 1
                    WHERE health_facility_id = f;
                    -- use this to add entry in extras table
                    SELECT submission_id INTO extras_id FROM rapidsms_xforms_xformsubmissionextras WHERE submission_id = NEW.id;
                    IF extras_id IS NULL THEN
                        INSERT INTO rapidsms_xforms_xformsubmissionextras (submission_id, facility_id, cdate, reporter_id)
                        VALUES(NEW.id, f, NOW(), hp);
                    END IF;
                END IF;
                RETURN NEW;
            ELSIF NEW.has_errors = TRUE AND OLD.has_errors = FALSE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports - 1
                    WHERE health_facility_id = f AND total_reports > 0;
                    -- use this to add entry in extras table
                    SELECT submission_id INTO extras_id FROM rapidsms_xforms_xformsubmissionextras WHERE submission_id = NEW.id;
                    IF extras_id IS NULL THEN
                        INSERT INTO rapidsms_xforms_xformsubmissionextras (submission_id, facility_id, cdate, reporter_id)
                        VALUES(NEW.id, f, NOW(), hp);
                    END IF;
                END IF;
                RETURN NEW;
            END IF;
            RETURN NEW;
        END IF;
    END;
$update_facility_extras$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_total_reporters() RETURNS TRIGGER AS $delim$
    DECLARE
    is_active BOOLEAN;
    new_loc INTEGER;
    BEGIN
        IF TG_OP = 'INSERT' THEN
            INSERT INTO healthmodels_healthproviderextras(health_provider_id,total_reports, district)
            VALUES(NEW.contact_ptr_id, 0, get_district(NEW.location_id));
            IF NEW.facility_id IS NOT NULL THEN
                --UPDATE healthmodels_healthfacilityextras SET total_reporters = total_reporters + 1
                    --WHERE health_facility_id = NEW.facility_id;
                NULL;
            END IF;
            RETURN NEW;
        ELSIF TG_OP = 'UPDATE' THEN
            IF NEW.facility_id <> OLD.facility_id THEN
                SELECT active INTO is_active FROM rapidsms_contact WHERE id = NEW.contact_ptr_id;
                IF is_active IS TRUE THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reporters = total_reporters + 1
                        WHERE health_facility_id = NEW.facility_id AND NEW.facility_id IS NOT NULL;
                    UPDATE healthmodels_healthfacilityextras SET total_reporters = total_reporters - 1
                        WHERE health_facility_id = OLD.facility_id AND total_reports > 0 AND OLD.facility_id IS NOT NULL;
                END IF;
            END IF;
            SELECT reporting_location_id INTO new_loc FROM rapidsms_contact WHERE id = NEW.contact_ptr_id;
            IF new_loc IS NOT NULL THEN
	            UPDATE healthmodels_healthproviderextras SET district = get_district(new_loc)
	     	    WHERE health_provider_id = NEW.contact_ptr_id;
            END IF;
            RETURN NEW;
        ELSE
            RETURN NULL;
        END IF;
    END;
$delim$ LANGUAGE plpgsql;

-- Added function and view to cater for outputing correct stuff in excell export -remeber user switching facility
CREATE OR REPLACE FUNCTION get_facility_district(fid INTEGER) RETURNS TEXT AS
$delim$
    DECLARE
    ca INTEGER;
    BEGIN
        SELECT location_id INTO ca FROM healthmodels_healthfacilitybase_catchment_areas WHERE
        healthfacilitybase_id = fid LIMIT 1;
        RETURN get_district(ca);
    END;
$delim$ LANGUAGE plpgsql;

DROP VIEW IF EXISTS xform_submissions_view_reviewed;
CREATE VIEW xform_submissions_view_reviewed AS
SELECT
    a.id AS report_id, b.name AS report, b.keyword, a.created AS "date",
    d.name AS reporter,
    e.reporter_id AS reporter_id, c.identity AS phone,
    get_facility_district(e.facility_id) AS district,
    get_facility_str(e.facility_id) AS facility,
    CASE WHEN a.has_errors IS TRUE THEN 'No' ELSE 'Yes' END AS valid,
    CASE WHEN a.approved IS TRUE THEN 'Yes' ELSE 'No' END AS approved
FROM rapidsms_xforms_xformsubmission a, rapidsms_xforms_xform b,
    rapidsms_connection c, rapidsms_contact d, rapidsms_xforms_xformsubmissionextras e
WHERE
    a.xform_id = b.id
    AND a.connection_id IS NOT NULL
    AND e.submission_id = a.id
    AND b.keyword
        IN ('com', 'mal', 'rutf', 'epi', 'home', 'birth', 'muac', 'opd', 'test', 'treat', 'rdt', 'act', 'qun', 'cases',
            'death','doc','med','sum', 'summary', 'vita', 'vacm', 'worm', 'anc', 'eid', 'dpt', 'redm', 'breg', 'tet')
    AND (a.connection_id = c.id AND c.contact_id = d.id)
    ORDER BY a.created DESC;

CREATE OR REPLACE FUNCTION rapidsms_xforms_xformsubmission_after_update() RETURNS TRIGGER AS
$delim$
    DECLARE
    last_confirmation_id INTEGER;
    BEGIN
        -- last_confirmation_id := 0;
        SELECT confirmation_id INTO last_confirmation_id FROM
        rapidsms_xforms_xformsubmission WHERE xform_id = NEW.xform_id ORDER BY confirmation_id DESC LIMIT 1;
        IF last_confirmation_id IS NOT NULL AND NEW.confirmation_id = 0 THEN
            UPDATE rapidsms_xforms_xformsubmission SET confirmation_id = last_confirmation_id + 1
            WHERE id = NEW.id;
        END IF;
        RETURN NEW;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER rapidsms_xforms_xformsubmission_after_update AFTER UPDATE ON rapidsms_xforms_xformsubmission
    FOR EACH ROW EXECUTE PROCEDURE rapidsms_xforms_xformsubmission_after_update();
