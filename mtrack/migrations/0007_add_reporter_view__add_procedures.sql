-- CREATE the necessary views
CREATE OR REPLACE FUNCTION get_facility_str(facility_id INT) RETURNS TEXT AS $delim$
    DECLARE
    xname TEXT;
    BEGIN
        SELECT INTO xname a.name || ' ' || b.name
        FROM
            healthmodels_healthfacilitybase a, healthmodels_healthfacilitytypebase b
        WHERE
            a.id = facility_id
            AND a.type_id = b.id;
        IF xname IS NULL THEN
            RETURN 'None';
        END IF;
        RETURN xname;
    END;
$delim$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_default_connection(_contact_id INT,return_conid BOOLEAN) RETURNS TEXT AS
$delim$
    DECLARE
    r TEXT;
    p TEXT;
    BEGIN
        SELECT identity,id INTO r,p FROM rapidsms_connection WHERE contact_id = _contact_id LIMIT 1;
        IF NOT FOUND THEN
            RETURN '';
        ELSE
            IF return_conid IS TRUE THEN
                RETURN r || ',' || p ;
            ELSE
                RETURN r;
            END IF;
        END IF;
    END;
$delim$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION contact_connections(_contact_id INT) RETURNS TEXT AS
$delim$
    DECLARE
    r TEXT;
    p TEXT;
    BEGIN
        r := '';
        FOR p IN SELECT identity FROM rapidsms_connection WHERE contact_id = _contact_id LOOP
            r := r || p || ',';
        END LOOP;
        RETURN rtrim(r,',');
    END;
$delim$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_reporter_groups(_contact_id INT) RETURNS TEXT AS
$delim$
    DECLARE
    r TEXT;
    p TEXT;
    BEGIN
        r := '';
        FOR p IN SELECT name FROM auth_group WHERE id IN (SELECT group_id FROM rapidsms_contact_groups WHERE contact_id = _contact_id) LOOP
            r := r || p || ',';
        END LOOP;
        RETURN rtrim(r,',');
    END;
$delim$ LANGUAGE plpgsql;

-- the reporters view
CREATE VIEW reporters AS
    SELECT r.id, r.name as name, r.active, r.village_name, r.reporting_location_id as reporting_location,
        get_default_connection(r.id, TRUE) AS default_connection,
        contact_connections(r.id) AS connections,
        get_reporter_groups(r.id) AS groups,
        p.facility_id, p.last_reporting_date,
        q.health_provider_id, q.total_reports, q.district,
        s.name AS loc_name,
        CASE WHEN p.facility_id IS NOT NULL THEN get_facility_str(p.facility_id) ELSE NULL END AS facility
    FROM healthmodels_healthproviderbase p, healthmodels_healthproviderextras q, rapidsms_contact r, locations_location s
    WHERE
        p.contact_ptr_id = q.health_provider_id
        AND r.id = p.contact_ptr_id
        AND r.reporting_location_id = s.id;

-- trigger function to update total reports from a facility - after insert or deleting
CREATE OR REPLACE FUNCTION update_facility_extras() RETURNS TRIGGER AS $update_facility_extras$
    DECLARE
    f INTEGER;
    hp INTEGER;
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
                RETURN NEW;
            END IF;
            IF NEW.has_errors = FALSE AND OLD.has_errors = TRUE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports + 1
                    WHERE health_facility_id = f;
                END IF;
                RETURN NEW;
            ELSIF NEW.has_errors = TRUE AND OLD.has_errors = FALSE THEN
                SELECT facility_id INTO f FROM healthmodels_healthproviderbase WHERE contact_ptr_id = hp;
                IF f IS NOT NULL THEN
                    UPDATE healthmodels_healthfacilityextras SET total_reports = total_reports - 1
                    WHERE health_facility_id = f;
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
	    UPDATE healthmodels_healthproviderextras SET district = get_district(NEW.location_id)
	     	WHERE health_provider_id = NEW.contact_ptr_id;
            RETURN NEW;
        ELSE
            RETURN NULL;
        END IF;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER update_total_reporters AFTER INSERT OR UPDATE ON healthmodels_healthproviderbase
    FOR EACH ROW EXECUTE PROCEDURE update_total_reporters();

-- create a trigger ---before deleting  from the healthmodels_healthproviderbase table
CREATE OR REPLACE FUNCTION healthprovider_before_delete() RETURNS trigger AS
$delim$
    DECLARE
    is_active BOOLEAN;
    BEGIN
        SELECT active INTO is_active FROM rapidsms_contact WHERE id = OLD.contact_ptr_id;
        IF OLD.facility_id IS NOT NULL AND is_active IS TRUE THEN
                UPDATE healthmodels_healthfacilityextras SET total_reporters = total_reporters - 1
                WHERE health_facility_id = OLD.facility_id AND total_reporters > 0;
        END IF;
        RETURN OLD;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER healthprovider_before_delete BEFORE DELETE ON healthmodels_healthproviderbase
    FOR EACH ROW EXECUTE PROCEDURE healthprovider_before_delete();

CREATE OR REPLACE FUNCTION rapidsms_contact_after_update() RETURNS trigger AS
$delim$
    DECLARE
    fid INT;
    BEGIN
        SELECT  facility_id INTO fid FROM healthmodels_healthproviderbase WHERE contact_ptr_id = NEW.id;
        IF fid IS NOT NULL THEN
            IF OLD.active <> NEW.active THEN
                IF NEW.active IS TRUE THEN
                    UPDATE  healthmodels_healthfacilityextras SET total_reporters = total_reporters + 1
                    WHERE health_facility_id = fid;
                ELSE
                    UPDATE  healthmodels_healthfacilityextras SET total_reporters = total_reporters - 1
                    WHERE health_facility_id = fid AND total_reporters > 0;
                END IF;
            END IF;
        END IF;
        RETURN NEW;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER rapidsms_contact_after_update AFTER UPDATE ON rapidsms_contact
    FOR EACH ROW EXECUTE PROCEDURE rapidsms_contact_after_update();

CREATE OR REPLACE FUNCTION healthfacilitybase_after_insert() RETURNS TRIGGER AS
$delim$
    DECLARE
    BEGIN
        INSERT INTO healthmodels_healthfacilityextras(health_facility_id, total_reports, total_reporters,catchment_areas_list)
        VALUES (NEW.id, 0, 0,'');
        RETURN NEW;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER healthfacilitybase_after_insert AFTER INSERT ON healthmodels_healthfacilitybase
    FOR EACH ROW EXECUTE PROCEDURE healthfacilitybase_after_insert();

