-- Shared physical output lifecycle; logical views own no business rules.

CREATE OR REPLACE FUNCTION guard_cost_projection_captured() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_state text; parent_basis text; member_basis text; n integer; m integer;
BEGIN
 IF COALESCE(NEW.projection_family, OLD.projection_family) = 'cost_generation' THEN
  IF TG_OP = 'INSERT' THEN
   IF NEW.state <> 'building' OR NOT EXISTS (
    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id
    AND id=NEW.captured_basis_id AND state='sealed') THEN
    RAISE EXCEPTION 'A report starts building from a sealed retained basis';
   END IF;
   RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
   IF EXISTS (SELECT 1 FROM cost_publication WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id) THEN
    RAISE EXCEPTION 'Published report cannot be discarded';
   END IF;
   DELETE FROM cost_inventory_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;
   DELETE FROM cost_contribution_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;
   RETURN OLD;
  END IF;
  IF OLD.state='sealed' OR NEW.tenant_id<>OLD.tenant_id OR NEW.id<>OLD.id
    OR NEW.captured_basis_id<>OLD.captured_basis_id OR NEW.scope_key<>OLD.scope_key THEN
   RAISE EXCEPTION 'Sealed report or report identity is immutable';
  END IF;
  IF NEW.state='sealed' THEN
   SELECT count(*) INTO n FROM cost_inventory_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
   SELECT count(*) INTO m FROM cost_contribution_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
   IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NOT EXISTS (
    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id AND id=NEW.captured_basis_id
    AND inventory_count=n AND contribution_count=m) THEN
    RAISE EXCEPTION 'Report membership is incomplete';
   END IF;
  END IF;
  RETURN NEW;
 END IF;
 IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_publication' THEN
  IF TG_OP='UPDATE' AND (OLD.tenant_id<>NEW.tenant_id OR OLD.scope_key<>NEW.scope_key OR OLD.id<>NEW.id) THEN
   RAISE EXCEPTION 'Publication scope is immutable';
  END IF;
  SELECT state INTO parent_state FROM cost_generation WHERE tenant_id=NEW.tenant_id
   AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;
  IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Publication requires sealed matching scope'; END IF;
  RETURN NEW;
 END IF;
 IF TG_OP='DELETE' AND pg_trigger_depth()=2 THEN RETURN OLD; END IF;
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Report rows are immutable'; END IF;
 SELECT state,captured_basis_id INTO parent_state,parent_basis FROM cost_generation
  WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;
 IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Report row requires building generation'; END IF;
 IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_inventory_row' THEN
  SELECT basis_id INTO member_basis FROM cost_captured_inventory_basis
   WHERE tenant_id=NEW.tenant_id AND id=NEW.inventory_basis_member_id;
 ELSE
  SELECT basis_id INTO member_basis FROM cost_captured_contribution_basis
   WHERE tenant_id=NEW.tenant_id AND id=NEW.contribution_basis_member_id;
 END IF;
 IF member_basis IS DISTINCT FROM parent_basis THEN RAISE EXCEPTION 'Report member belongs to another basis'; END IF;
 RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION guard_cost_projection_company() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE parent_state text; manifest_state text; n integer; m integer;
        BEGIN
          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_manifest' THEN
            IF TG_OP='INSERT' AND NEW.state<>'building' THEN
              RAISE EXCEPTION 'Company manifest starts building';
            END IF;
            IF TG_OP='UPDATE' AND (OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.census_id<>OLD.census_id OR NEW.scope_key<>OLD.scope_key) THEN
              RAISE EXCEPTION 'Sealed company manifest or identity is immutable';
            END IF;
            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
          END IF;
          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_generation' THEN
            IF TG_OP='INSERT' THEN
              SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id;
              IF NEW.state<>'building' OR manifest_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Generation requires sealed manifest'; END IF;
            ELSIF TG_OP='UPDATE' THEN
              IF OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.manifest_id<>OLD.manifest_id OR NEW.scope_key<>OLD.scope_key THEN RAISE EXCEPTION 'Sealed company generation or identity is immutable'; END IF;
              IF NEW.state='sealed' THEN
                SELECT count(*) INTO n FROM cost_company_inventory_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
                SELECT count(*) INTO m FROM cost_company_contribution_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
                IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NEW.completed_work_count<>NEW.expected_work_count THEN RAISE EXCEPTION 'Company generation membership is incomplete'; END IF;
              END IF;
            END IF;
            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
          END IF;
          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_publication' THEN
            IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.scope_key<>OLD.scope_key) THEN RAISE EXCEPTION 'Company publication scope is immutable'; END IF;
            SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;
            IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Company publication requires sealed generation'; END IF;
            RETURN NEW;
          END IF;
          IF COALESCE(NEW.projection_family, OLD.projection_family) IN ('cost_company_inventory_input','cost_company_contribution_input') THEN
            IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company manifest members are immutable'; END IF;
            SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id FOR UPDATE;
            IF manifest_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company input requires building manifest'; END IF;
            RETURN NEW;
          END IF;
          IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company generation members are immutable'; END IF;
          SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;
          IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company result requires building generation'; END IF;
          RETURN NEW;
        END $$;

CREATE OR REPLACE FUNCTION guard_cost_projection_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.tenant_id,NEW.projection_family,NEW.id) IS DISTINCT FROM (OLD.tenant_id,OLD.projection_family,OLD.id) THEN
  RAISE EXCEPTION 'Cost projection identity is immutable';
 END IF;
 RETURN NEW;
END $$;

CREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_generation FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();

CREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();

CREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();

CREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_publication FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();

CREATE TRIGGER guard_cost_generation_insert BEFORE INSERT ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_generation_update BEFORE UPDATE ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_generation_delete BEFORE DELETE ON cost_projection_generation FOR EACH ROW WHEN (OLD.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_inventory_row_insert BEFORE INSERT ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_inventory_row_update BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_inventory_row_delete BEFORE DELETE ON cost_projection_inventory FOR EACH ROW WHEN (OLD.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_contribution_row_insert BEFORE INSERT ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_contribution_row_update BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_contribution_row_delete BEFORE DELETE ON cost_projection_contribution FOR EACH ROW WHEN (OLD.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_publication_insert BEFORE INSERT ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_publication') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_publication_update BEFORE UPDATE ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_publication') EXECUTE FUNCTION guard_cost_projection_captured();

CREATE TRIGGER guard_cost_company_generation_insert BEFORE INSERT ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_generation_update BEFORE UPDATE ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_generation_delete BEFORE DELETE ON cost_projection_generation FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_inventory_result_insert BEFORE INSERT ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_inventory_result_update BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_inventory_result_delete BEFORE DELETE ON cost_projection_inventory FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_contribution_result_insert BEFORE INSERT ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_contribution_result_update BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_contribution_result_delete BEFORE DELETE ON cost_projection_contribution FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_publication_insert BEFORE INSERT ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_publication') EXECUTE FUNCTION guard_cost_projection_company();

CREATE TRIGGER guard_cost_company_publication_update BEFORE UPDATE ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_publication') EXECUTE FUNCTION guard_cost_projection_company();
