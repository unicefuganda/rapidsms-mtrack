CREATE VIEW facilities AS
    SELECT a.id, a.name AS name, b.name AS "type", a.district,
        a.owner, a.authority,
        a.last_reporting_date, c.total_reports, c.total_reporters,
        c.catchment_areas_list AS catchment_areas
    FROM
        healthmodels_healthfacilitybase a,
        healthmodels_healthfacilitytypebase b,
        healthmodels_healthfacilityextras c
    WHERE
        a.id = c.health_facility_id AND a.type_id = b.id;

-- used to update facility's total reports where submission is added,modified or deleted
CREATE OR REPLACE FUNCTION update_facility_extras() RETURNS TRIGGER AS $update_facility_extras$
    DECLARE
    f INTEGER;
    hp INTEGER;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            SELECT contact_id INTO hp FROM rapidsms_connection WHERE id = OLD.connection_id;
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

CREATE TRIGGER update_facility_extras AFTER INSERT OR UPDATE OR DELETE ON rapidsms_xforms_xformsubmission
    FOR EACH ROW EXECUTE PROCEDURE update_facility_extras();

--neatly update catchment_areas_list in the healthmodels_healthfacilityextras table
CREATE OR REPLACE FUNCTION edit_healthfacility() RETURNS TRIGGER AS $delim$
    DECLARE
    fid INTEGER;
    ret TEXT;
    fname TEXT;
    BEGIN
        ret := ''::text;
        fid := NEW.healthfacilitybase_id;
        IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
            FOR fname IN SELECT name FROM locations_location WHERE id IN (SELECT location_id
                FROM healthmodels_healthfacilitybase_catchment_areas WHERE healthfacilitybase_id = fid) LOOP
                ret := ret || fname::text || ','::text;
            END LOOP;
            UPDATE healthmodels_healthfacilityextras SET catchment_areas_list = rtrim(ret,',')
            WHERE health_facility_id = fid;
        END IF;
        RETURN NEW;
    END;
$delim$ LANGUAGE plpgsql;

CREATE TRIGGER edit_healthfacility AFTER INSERT OR UPDATE ON healthmodels_healthfacilitybase_catchment_areas
    FOR EACH ROW EXECUTE PROCEDURE edit_healthfacility();
