/*------------------------------------------------------------------------------------------------
  load_records.sas - reads the ctcae-lab-validation tables into WORK datasets (SAS 9.4 or later)

  %ctcval_load(dir=<folder that holds data/records.csv>, naming=NEUTRAL, prefix=ctcval_)

  Creates, with the default prefix:
    ctcval_records       one row per laboratory record (data/records.csv), DATE and REF_DATE as SAS dates
    ctcval_expectations  expected grades per record x version x profile x direction (data/expectations.csv)
    ctcval_criteria      machine-readable CTCAE criteria (data/criteria.csv)
    ctcval_conventions   reading conventions behind the expectations (data/conventions.csv)

  naming=ADAM renames the input columns of ctcval_records to ADaM names:
    SUBJECT_ID=USUBJID LBTESTCD=PARAMCD LBTEST=PARAM VAL=AVAL UNIT=AVALU LLN=ANRLO ULN=ANRHI DATE=ADT
    STUDY_DAY=ADY REF_DATE=TRTSDT BASELINE_FLAG=ABLFL BASE_VAL=BASE BASE_LLN=BNRLO BASE_ULN=BNRHI
  naming=SDTM renames them to SDTM names (dates become ISO 8601 character values):
    SUBJECT_ID=USUBJID VAL=LBSTRESN UNIT=LBSTRESU LLN=LBSTNRLO ULN=LBSTNRHI DATE=LBDTC STUDY_DAY=LBDY
    REF_DATE=RFSTDTC BASELINE_FLAG=LBBLFL STATUS=LBSTAT
  The EXP_* expectation columns and the SI / conventional views keep their names under every naming.
------------------------------------------------------------------------------------------------*/
%macro ctcval_load(dir=, naming=NEUTRAL, prefix=ctcval_);
  %local d n;
  %let d=%sysfunc(dequote(&dir));
  %if %length(&d)=0 %then %do;
    %put ERROR: ctcval_load - give dir= the folder that holds data/records.csv;
    %return;
  %end;
  %let naming=%upcase(&naming);

  data &prefix.records;
    infile "&d/data/records.csv" dsd dlm=',' firstobs=2 lrecl=4096 truncover encoding="utf-8";
    length RECORD_ID 8 SUBJECT_ID $20 SCENARIO_ID $24 MODULE $8 RULE_IDS $200 LBTESTCD $8 LBTEST $40 LBSPEC $6 LBDUR $5
           VAL 8 UNIT $16 LLN 8 ULN 8 VAL_SI 8 UNIT_SI $16 LLN_SI 8 ULN_SI 8 VAL_CONV 8 UNIT_CONV $16 LLN_CONV 8 ULN_CONV 8
           DATE 8 STUDY_DAY 8 REF_DATE 8 BASELINE_FLAG $1 BASE_VAL 8 BASE_UNIT $16 BASE_LLN 8 BASE_ULN 8
           BASE_VAL_SI 8 BASE_LLN_SI 8 BASE_ULN_SI 8 BASE_VAL_CONV 8 BASE_LLN_CONV 8 BASE_ULN_CONV 8
           STATUS $8 GRADABLE $1
           EXP_GRADE_LOW_V5 8 EXP_GRADE_HIGH_V5 8 EXP_TERM_LOW_V5 $60 EXP_TERM_HIGH_V5 $60
           EXP_BASE_GRADE_LOW_V5 8 EXP_BASE_GRADE_HIGH_V5 8 EXP_GRADE_V5 8 EXP_TERM_V5 $60
           EXP_GRADE_LOW_V6 8 EXP_GRADE_HIGH_V6 8 EXP_TERM_LOW_V6 $60 EXP_TERM_HIGH_V6 $60
           EXP_BASE_GRADE_LOW_V6 8 EXP_BASE_GRADE_HIGH_V6 8 EXP_GRADE_V6 8 EXP_TERM_V6 $60
           VERSION_DELTA $1 CONVENTIONS $200 CONVENTION_DEP $1 DESCRIPTION $120;
    informat DATE REF_DATE yymmdd10.;
    format DATE REF_DATE yymmdd10.;
    input RECORD_ID SUBJECT_ID $ SCENARIO_ID $ MODULE $ RULE_IDS $ LBTESTCD $ LBTEST $ LBSPEC $ LBDUR $
          VAL UNIT $ LLN ULN VAL_SI UNIT_SI $ LLN_SI ULN_SI VAL_CONV UNIT_CONV $ LLN_CONV ULN_CONV
          DATE STUDY_DAY REF_DATE BASELINE_FLAG $ BASE_VAL BASE_UNIT $ BASE_LLN BASE_ULN
          BASE_VAL_SI BASE_LLN_SI BASE_ULN_SI BASE_VAL_CONV BASE_LLN_CONV BASE_ULN_CONV
          STATUS $ GRADABLE $
          EXP_GRADE_LOW_V5 EXP_GRADE_HIGH_V5 EXP_TERM_LOW_V5 $ EXP_TERM_HIGH_V5 $
          EXP_BASE_GRADE_LOW_V5 EXP_BASE_GRADE_HIGH_V5 EXP_GRADE_V5 EXP_TERM_V5 $
          EXP_GRADE_LOW_V6 EXP_GRADE_HIGH_V6 EXP_TERM_LOW_V6 $ EXP_TERM_HIGH_V6 $
          EXP_BASE_GRADE_LOW_V6 EXP_BASE_GRADE_HIGH_V6 EXP_GRADE_V6 EXP_TERM_V6 $
          VERSION_DELTA $ CONVENTIONS $ CONVENTION_DEP $ DESCRIPTION $;
    label RECORD_ID='Record key' SUBJECT_ID='Synthetic subject' SCENARIO_ID='Scenario' MODULE='Validation module'
          RULE_IDS='criteria.csv rules exercised' VAL='Result as received' UNIT='Unit as received'
          LLN='Lower limit of normal as received' ULN='Upper limit of normal as received'
          DATE='Collection date' STUDY_DAY='Study day' REF_DATE='Reference date (first dose)'
          BASELINE_FLAG='Baseline record flag' STATUS='NOT DONE marker' GRADABLE='A grade is expected (Y/N)'
          VERSION_DELTA='v5 and v6 expectations differ (Y/N)' CONVENTIONS='Conventions relied on'
          CONVENTION_DEP='Expectation depends on a disputed convention (Y/N)' DESCRIPTION='What the record proves';
  run;

  data &prefix.expectations;
    infile "&d/data/expectations.csv" dsd dlm=',' firstobs=2 lrecl=1024 truncover encoding="utf-8";
    length RECORD_ID 8 VERSION 8 PROFILE $20 DIRECTION $5 GRADE 8 TERM $60 BASE_GRADE 8;
    input RECORD_ID VERSION PROFILE $ DIRECTION $ GRADE TERM $ BASE_GRADE;
  run;

  data &prefix.criteria;
    infile "&d/data/criteria.csv" dsd dlm=',' firstobs=2 lrecl=4096 truncover encoding="utf-8";
    length RULE_ID $24 CLAUSE_SEQ 8 VERSION 8 LBTESTCD $8 LBSPEC $6 CTCAE_TERM $60 SOC $40 DIRECTION $4 BASELINE_ARM $9
           GRADE 8 LAB_DERIVABLE $1 WORDING $200 CLAUSE $200 COMPARATOR $2 OPERAND $20 THRESHOLD $10 THRESHOLD_UNIT $16
           THRESHOLD_CONV $10 THRESHOLD_CONV_UNIT $16 CONDITION $10 QUALIFIER $20 CONVENTION $80 SOURCE_DOC $80
           SOURCE_PAGE 8 NOTE $200;
    input RULE_ID $ CLAUSE_SEQ VERSION LBTESTCD $ LBSPEC $ CTCAE_TERM $ SOC $ DIRECTION $ BASELINE_ARM $ GRADE LAB_DERIVABLE $
          WORDING $ CLAUSE $ COMPARATOR $ OPERAND $ THRESHOLD $ THRESHOLD_UNIT $ THRESHOLD_CONV $ THRESHOLD_CONV_UNIT $
          CONDITION $ QUALIFIER $ CONVENTION $ SOURCE_DOC $ SOURCE_PAGE NOTE $;
  run;

  data &prefix.conventions;
    infile "&d/data/conventions.csv" dsd dlm=',' firstobs=2 lrecl=8192 truncover encoding="utf-8";
    length CONVENTION $24 SCOPE $8 TITLE $60 CTCAE_WORDING $600 DEFAULT_CHOICE $600 ALTERNATIVE_CHOICE $300
           ALTERNATIVE_PROFILE $20 VERSIONS $3 LBTESTCD $60 CONVENTION_DEP $1 NOTE $200;
    input CONVENTION $ SCOPE $ TITLE $ CTCAE_WORDING $ DEFAULT_CHOICE $ ALTERNATIVE_CHOICE $ ALTERNATIVE_PROFILE $
          VERSIONS $ LBTESTCD $ CONVENTION_DEP $ NOTE $;
  run;

  %if &naming=ADAM %then %do;
    proc datasets lib=work nolist;
      modify &prefix.records;
        rename SUBJECT_ID=USUBJID LBTESTCD=PARAMCD LBTEST=PARAM VAL=AVAL UNIT=AVALU LLN=ANRLO ULN=ANRHI DATE=ADT
               STUDY_DAY=ADY REF_DATE=TRTSDT BASELINE_FLAG=ABLFL BASE_VAL=BASE BASE_LLN=BNRLO BASE_ULN=BNRHI;
      run;
    quit;
  %end;
  %else %if &naming=SDTM %then %do;
    data &prefix.records;
      set &prefix.records(rename=(SUBJECT_ID=USUBJID VAL=LBSTRESN UNIT=LBSTRESU LLN=LBSTNRLO ULN=LBSTNRHI
                                  STUDY_DAY=LBDY BASELINE_FLAG=LBBLFL STATUS=LBSTAT));
      length LBDTC RFSTDTC $10;
      LBDTC=put(DATE, yymmdd10.);
      RFSTDTC=put(REF_DATE, yymmdd10.);
      drop DATE REF_DATE;
    run;
  %end;
  %else %if &naming ne NEUTRAL %then %put WARNING: ctcval_load - naming=&naming is not NEUTRAL, ADAM or SDTM and was ignored;

  %let n=0;
  data _null_;
    if 0 then set &prefix.records nobs=nobs;
    call symputx('n', nobs);
    stop;
  run;
  %put NOTE: ctcval_load - &n records loaded from &d/data/records.csv with naming=&naming;
%mend ctcval_load;
