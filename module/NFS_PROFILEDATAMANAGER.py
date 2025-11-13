import logging
import pandas as pd
import re
import os
from . import NFS_DATAFRAME as NFS_DF
from . import NFS_STRPROFILE as NFS_SP
from typing import Self, Optional, Literal

logger = logging.getLogger(__name__)

class NFSProfileDataManager:
    """프로필 데이터 관리 클래스

    Attributes:
        df_profile(pd.DataFrame): 프로필 데이터를 저장하는 데이터프레임
        kit(str): 실험에 사용한 키트
    """

    # 키트마다 사용하는 좌위 마커를 감정서 표에 나열되는 순서대로 작성한 리스트.
    DICT_MARKERS = {
        "STR": [
            "AMEL",
            "D3S1358",
            "vWA",
            "D16S539",
            "CSF1PO",
            "TPOX",
            "D8S1179",
            "D21S11",
            "D18S51",
            "D2S441",
            "D19S433",
            "TH01",
            "FGA",
            "D22S1045",
            "D5S818",
            "D13S317",
            "D7S820",
            "D10S1248",
            "D1S1656",
            "D12S391",
            "D2S1338",
            "Penta E",
            "Penta D",
            "SE33",
        ],
        "YSTR": [
            "DYS576",
            "DYS389 I",
            "DYS448",
            "DYS389 II",
            "DYS19",
            "DYS391",
            "DYS481",
            "DYS533",
            "DYS438",
            "DYS437",
            "DYS570",
            "DYS635",
            "DYS390",
            "DYS439",
            "DYS392",
            "DYS393",
            "DYS458",
            "DYS385",
            "DYS456",
            "Y GATA H4",
        ],
    }
    PROB_NOMATCH = (
        0.0003  # Allele frequency 테이블 존재하지 않는 좌위 위치 frequency의 대체값
    )
    TA_THRESHOLD = 2  # 혼합 프로필 판단시 Tri-allelic 허용 개수.

    def __init__(self, kit: Literal["STR", "YSTR"] = "STR"):
        logger.info(f"NFSProfileDataManager 초기화 시작 (kit={kit})")
        self.df_profile = pd.DataFrame()
        self.kit:Literal["STR", "YSTR"] = kit
        # 모듈 파일이 있는 디렉토리를 기준으로 CSV 파일 경로 설정
        module_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(module_dir, "allele_frequency.csv")
        logger.debug(f"allele_frequency.csv 로딩 중: {csv_path}")
        self.allele_frequency = pd.read_csv(csv_path)
        logger.info(f"NFSProfileDataManager 초기화 완료 (kit={kit}, allele_frequency rows={len(self.allele_frequency)})") 

    def load_combined_result_from_tomato(self, path: str) -> None:
        """Tomato 엑셀 파일의 Cominbed_result를 데이터프레임으로 불러오고 분석이 용이한 형태로 가공한다.

        Args:
            path(str): 읽어올 토마토 파일 경로
        """
        logger.info(f"Tomato 파일 로딩 시작: {path}")

        def analyze_status_combined() -> None:
            """프로필 데이터가 합쳐진 상태를 분석해서 정리"""
            df_tomato["STATUS_COMBINED"] = "DEFAULT"
            # 한번만 실험한 데이터 = UNIQUE
            df_tomato.loc[
                ~df_tomato["Sample Name"].duplicated(keep=False), "STATUS_COMBINED"
            ] = "UNIQUE"
            # 여러번 실험한 데이터가 합쳐진 데이터(Sample ID가 공란) = CROSSCHECKED.
            df_tomato.loc[df_tomato["Sample ID"].isna(), "STATUS_COMBINED"] = (
                "CROSSCHECKED"
            )
            # 추정형을 위해 복사된 데이터('Sample ID가 'Duplicated~' = DUPLICATED.
            df_tomato.loc[
                df_tomato["Sample ID"] == "Duplicated data of above line",
                "STATUS_COMBINED",
            ] = "DUPLICATED"
            # 복사된 데이터는 Sample Name에 '+'를 추가해 별개의 프로필로 취급.
            df_tomato.loc[
                df_tomato["STATUS_COMBINED"] == "DUPLICATED", "Sample Name"
            ] = (
                df_tomato.loc[
                    df_tomato["STATUS_COMBINED"] == "DUPLICATED", "Sample Name"
                ]
                + "+"
            )

        def preprocess_df_tomato(df_input: pd.DataFrame) -> pd.DataFrame:
            """토마토 데이터프레임 전처리
            Args:
                df_input(pd.DataFrame): 토마토 데이터프레임
            Returns:
                pd.DataFrame: 전처리가된 토마토 데이터프레임
            """
            df = df_input.copy()
            # Sample Name이 사건번호의 포멧에 일치하는 데이터만 남김
            p = re.compile(r"\d+[-]\w[-]\d+")  # e.g 2023-D-1234
            cond1 = df["Sample Name"].apply(lambda x: True if p.match(x) else False)
            df = df[cond1]
            # 칼럼명 변경
            df.rename(
                {
                    "Case Number": "접수번호",
                    "Sample Name": "감정물번호",
                    "Amelogenin": "AMEL",
                },
                axis="columns",
                inplace=True,
            )
            # 필요한 데이터만 추출.
            df = df[
                ["접수번호", "감정물번호", "STATUS_COMBINED"]
                + self.DICT_MARKERS[self.kit]
            ]
            df = df.loc[df["STATUS_COMBINED"] != "DEFAULT"]
            df.fillna("", inplace=True)
            df = NFS_DF.sort_by_serial_number(df, key_column="감정물번호")
            # 테스트용 데이터 생성, 기능 추가 후 삭제
            return df

        df_tomato = pd.read_excel(path, sheet_name="CombinedResult", header=1)
        logger.debug(f"엑셀 파일 읽기 완료 (rows={len(df_tomato)})")
        analyze_status_combined()
        self.df_profile = preprocess_df_tomato(df_tomato)
        logger.info(f"Tomato 파일 로딩 완료 (최종 프로필 수={len(self.df_profile)})")

    def export_df_in_set(self, STR_20: bool = False) -> pd.DataFrame:
        """STR탭에서 데이터 분석을 위해 좌위 정보를 str에서 set로 변환해서 데이터프레임 반환
        e.g: 23-24 -> (23, 24), 12 -> (12)

        Args:
            STR_20(bool): 감정서 표준인 20좌위만 추출해서 반환.
        Returns:
            pd.DataFrame: 변환된 df_profile
        """

        df_profile = self.df_profile.copy()
        list_markers = (
            self.DICT_MARKERS[self.kit][:-3] if STR_20 else self.DICT_MARKERS[self.kit]
        )
        for marker in list_markers:
            df_profile[marker] = df_profile[marker].apply(
                lambda x: set(str(x).split("-")) if x != "" else set()
            )
        return df_profile

    def concatenate(self, new_NPDM) -> None:
        """새로 불러온 NFSProfileDataManager의 데이터를 기존 객체에 추가.
        병합 가능성을 확인. 중복된 데이터의 경우 기존 데이터 보존

        Args:
            new_NPDM(NFSProfileDataManager): 새로 추가할 데이터를 가진 NFSProfileDataManager
        """

        def count_allele(row):
            cnt = 0
            for col in self.DICT_MARKERS[self.kit]:
                if not pd.isna(row[col]):
                    cnt = cnt + 1
            return cnt

        if self.kit != new_NPDM.kit or len(
            set(self.df_profile.columns).difference(set(new_NPDM.df_profile.columns))
        ):
            print("기존 객체와 키트 또는 칼럼 상태가 다릅니다.")
        else:
            concat_profile = pd.concat(
                [self.df_profile, new_NPDM.df_profile], axis=0
            ).reset_index(drop=True)
            concat_profile["CNT_ALLELE"] = concat_profile.apply(count_allele, axis=1)
            # 중복값이 존재하는 감정물번호를 추출
            sn_duplicated = concat_profile.loc[
                concat_profile.duplicated(subset="감정물번호", keep=False), "감정물번호"
            ].unique()
            # 구조상 1:1 비교만 존재하므로 감정물 번호의 첫번째 데이터와 두번째 데이터를 비교
            list_drop_idx = []
            for sn in sn_duplicated:
                data_old = concat_profile[concat_profile["감정물번호"] == sn].iloc[0]
                data_new = concat_profile[concat_profile["감정물번호"] == sn].iloc[1]
                if (
                    data_old["STATUS_COMBINED"] == "CROSSCHECKED"
                    and data_new["STATUS_COMBINED"] == "CROSSCHECKED"
                ):
                    if data_old["CNT_ALLELE"] > data_new["CNT_ALLELE"]:
                        list_drop_idx.append(data_new.name)
                    else:
                        list_drop_idx.append(data_old.name)
                elif (
                    data_old["STATUS_COMBINED"] == "CROSSCHECKED"
                    and data_new["STATUS_COMBINED"] == "UNIQUE"
                ):
                    list_drop_idx.append(data_new.name)
                else:
                    list_drop_idx.append(data_old.name)
            df_drop = concat_profile.drop(index=list_drop_idx, axis=0).reset_index(
                drop=True
            )
            df_drop = df_drop.drop("CNT_ALLELE", axis=1)
            self.df_profile = NFS_DF.sort_by_serial_number(
                df_drop, key_column="감정물번호"
            )

    def filter_by_codecase(self, code_case:str) -> Optional[Self]:
        """접수번호로 프로필 데이터를 필터하고 프로필 데이터매니저를 반환한다"""
        logger.debug(f"접수번호로 필터링 시작 (code_case={code_case})")

        try:
            df_profile_by_codecase = self.df_profile.loc[self.df_profile['접수번호']==code_case, :].reset_index(drop=True)
            logger.info(f"필터링 완료 (code_case={code_case}, 프로필 수={len(df_profile_by_codecase)})")
            return self._get_instance(kit=self.kit, df_profile=df_profile_by_codecase)
        except KeyError as e:
            logger.error(f"KeyError: {e} - {code_case}의 증거물 정보가 데이터프레임에 존재하지 않습니다.")
            print(f"{e} : {code_case}의 증거물 정보가 데이터프레임에 존재하지 않습니다.")
        
        
    @classmethod
    def _get_instance(cls, kit:Literal["STR", "YSTR"] , df_profile:pd.DataFrame) -> Self:
        """프로필 데이터매니저 생성하고 반환한다. 내부에서 인스턴스를 정의하고 반환하는 목적의 내장함수."""
        pdm = cls(kit=kit)
        pdm.df_profile = df_profile.copy()
        return pdm

    def length(self) -> int:
        return self.df_profile.shape[0]

    def extract_gender_from_profile(self, code_evidence: str) -> str:
        """해당 감정물번호에 해당하는 프로필의 성별을 반환한다.
        Args:
            code_evidence(str): 감정물번호
        Returns:
            str: 여성 or 남성
        """
        amelogenin = self.df_profile[
            self.df_profile["감정물번호"] == code_evidence
        ].iloc[0]["AMEL"]
        gender = "여성" if amelogenin == "X" else "남성"
        logger.debug(f"성별 추출 완료 (code_evidence={code_evidence}, gender={gender})")
        return gender

    def calculate_likelihood_from_profile(self, code_evidence: str) -> tuple:
        """입력받은 감정물 번호에 해당하는 프로필의 개인식별지수를 계산하여 반환한다
        Args:
            code_evidence(str): 감정물번호
        Returns:
            str: 감정서 폼으로 쓰여진 개인식별지수, 1.00x10^지수
        """
        logger.debug(f"개인식별지수 계산 시작 (code_evidence={code_evidence})")
        prob_match = 1.0
        list_marker = self.DICT_MARKERS["GF/PPF"][:-3]
        profile = self.df_profile[self.df_profile["감정물번호"] == code_evidence].iloc[
            0
        ]
        for marker in list_marker:
            if profile[marker] != "":
                frequencies = []
                alleles = str(profile[marker]).split("-")
                for allele in alleles:
                    try:
                        float_allele = float(allele)
                        cond1 = self.allele_frequency["Loci"] == marker
                        cond2 = self.allele_frequency["Allele"] == float_allele
                        df_frequency = self.allele_frequency[cond1 & cond2]
                        if df_frequency.shape[0]:
                            frequencies.append(df_frequency.iloc[0]["Frequency"])
                        else:
                            frequencies.append(self.PROB_NOMATCH)
                    except ValueError:
                        continue
                if len(frequencies):
                    if len(alleles) == 1:
                        prob_match = prob_match / (frequencies[0] * frequencies[0])
                    else:
                        prob_match = prob_match / (2 * frequencies[0] * frequencies[1])
        text_prob = "{0:.2e}".format(
            prob_match
        )  # '40800000000.00000000000000'-> '4.08e+10'
        text_prob = (
            text_prob[:3] + text_prob[4:]
        )  # 4.08e+10 -> 4.0e+10 버림 연산을 대체.
        result = tuple(text_prob.split("e+"))
        logger.info(f"개인식별지수 계산 완료 (code_evidence={code_evidence}, LR={result[0]}x10^{result[1]})")
        return result

    def export_to_str(
        self, code_evidence: str, list_marker: list, y23: bool = True
    ) -> tuple:
        """감정물번호의 프로필을 문자열로 구성된 프로필 딕셔너리 형태로 반환하고, 프로필 내 특이사항을 리스트로 정리해 반환한다.

        Args:
            code_evidence: 감정물 유형. e.g. 대조, 대표, NC, ND
            list_marker: 사용할 좌위 마커 리스트
            flag_homo_duplication: homologous 좌위값을 반복된 형태로 표시할지 여부(e.g 12 -> 12-12)
        Returns:
            tuple: (dict, list) = (문자열로 구성된 프로필 딕셔너리, 프로필내 특이사항 리스트)
        """

        def check_mixture() -> bool:
            """현재 작업중인 프로필이 혼합 프로필인지 검사
            Returns:
                bool: 혼합 프로필 여부
            """
            limit_allele = 1 if y23 else 2
            cnt_ta = 0
            for marker in list_marker:
                alleles = series_profile[marker]
                cnt_ta = cnt_ta + 1 if len(alleles) > limit_allele else cnt_ta
            return True if cnt_ta > self.TA_THRESHOLD else False

        def check_special_case(locus: str, allele: str) -> bool:
            """비정형 좌위값 중 허용되는 특수 케이스인지 여부를 체크하고 반환한다.
            Args:
                locus: 좌위
                allele: 좌위값
            Returns:
                bool: 특수 케이스 여부
            """
            if locus in self.DICT_MARKERS["Y23"]:
                return True
            decimal_place = allele.split(".")[1]
            if decimal_place == "2":
                return True
            if locus == "TH01" and allele == "9.3":
                return True
            elif locus == "D2S441" and allele == "9.1":
                return True
            elif locus == "D1S1656" and (allele == "17.3" or allele == "18.3"):
                return True
            elif locus == "Penta E" and (decimal_place == "2" or decimal_place == "3"):
                return True
            elif locus == "Penta D" and (decimal_place == "2" or decimal_place == "3"):
                return True
            else:
                return False

        def transform_set_to_list(set_input: set) -> list:
            """
            Allele 값이 저장된 집합 데이터를 -값으로 이어 하나의 string으로 만들고 반환
            Args:
                set_input(Set): 입력된 좌위 세트
            """

            def is_number(string: str) -> bool:
                try:
                    float(string)
                    return True
                except (ValueError, OverflowError):
                    return False

            num_input = list(filter(is_number, set_input))
            num_input.sort(key=float)
            str_input = list(filter(lambda x: not is_number(x), set_input))
            str_input.sort()
            if str_input:
                return str_input
            else:
                return [str(s) for s in num_input]

        string_profile = {}
        flag_NC = False
        flag_ND = False
        cnt_microvariant = 0
        str_etc = []
        str_etc_microvariant = []
        temp_profile = {}
        # NC, ND 프로필 처리
        if code_evidence == "ND":
            for locus in list_marker:
                string_profile[locus] = "ND"
            str_etc = ["ND : 디엔에이형이 검출되지 않음."]
            return string_profile, str_etc
        elif code_evidence == "NC":
            for locus in list_marker:
                string_profile[locus] = "NC"
            str_etc = ["NC : 디엔에이형을 결정할 수 없음."]
            return string_profile, str_etc
        # 대조, 대표 처리
        df_profile = self.export_df_in_set().copy()
        series_profile = df_profile[df_profile["감정물번호"] == code_evidence].iloc[0]
        for locus in list_marker:
            alleles = transform_set_to_list(set(series_profile[locus]))
            temp_alleles = []
            if len(alleles) == 0:
                temp_alleles.append("NC")
                flag_NC = True
            elif alleles[0] == "ND":
                temp_alleles.append("ND")
                flag_ND = True
            elif alleles[0] == "NC":
                temp_alleles.append("NC")
                flag_NC = True
            else:
                for allele in alleles:
                    if allele.find("OL") != -1:
                        continue
                    modified_allele = allele
                    if allele.find(".") != -1:
                        if not check_special_case(locus, allele):
                            cnt_microvariant = cnt_microvariant + 1
                            decimal_place = allele.split(".")[1]
                            if decimal_place == "1":
                                modified_allele = str(int(float(allele)))
                            else:
                                modified_allele = str(int(float(allele) + 1))
                            modified_allele = modified_allele + "*" * cnt_microvariant
                            str_etc_microvariant.append(
                                "*" * cnt_microvariant
                                + " : 미세변이 (검출값 : {0})".format(allele)
                            )
                    temp_alleles.append(modified_allele)
            temp_profile[locus] = temp_alleles
        if check_mixture():
            str_etc.append("/ : 혼합 디엔에이형.")
            for locus, alleles in temp_profile.items():
                string_profile[locus] = "/".join([str(element) for element in alleles])
        else:
            for locus, alleles in temp_profile.items():
                if not y23 and len(alleles) == 1 and alleles[0] != "NC":
                    alleles = alleles * 2
                string_profile[locus] = "-".join([str(element) for element in alleles])
                # 특수 케이스
                if locus == "AMEL":
                    string_profile[locus] = string_profile[locus].replace("-", "")
                if locus == "DYS385":
                    string_profile[locus] = string_profile[locus].replace("-", ", ")
        str_etc = str_etc + str_etc_microvariant
        if flag_ND:
            str_etc.append("ND : 디엔에이형이 검출되지 않음.")
        if flag_NC:
            str_etc.append("NC : 디엔에이형을 결정할 수 없음.")
        return string_profile, str_etc

    def generate_STRProfile(
        self, samplename: str, STR_20: bool = False
    ) -> NFS_SP.STRProfile:
        """
        샘플명과 키트 정보를 바탕으로 STR 프로파일 객체를 생성합니다.

        Args:
            samplename (str): 감정물 번호/샘플 이름
            STR_20 (bool, optional): 20개 마커 사용 여부. 기본값은 False.

        Returns:
            STRProfile: 생성된 STR 프로파일 객체

        Raises:
            ValueError: 샘플명이 데이터에서 찾을 수 없는 경우

        Examples:
            >>> profile = self.generate_STRProfile("S001", STR_20=True)
            >>> print(profile.id)
            S001
        """
        logger.debug(f"STRProfile 생성 시작 (samplename={samplename}, STR_20={STR_20})")
        # 마커 리스트 결정
        list_markers = (
            self.DICT_MARKERS[self.kit][:-3] if STR_20 else self.DICT_MARKERS[self.kit]
        )

        # 샘플 데이터 조회 (예외 처리 추가)
        sample_data = self.df_profile[self.df_profile["감정물번호"] == samplename]
        if sample_data.empty:
            logger.error(f"ValueError: 샘플 '{samplename}'을 찾을 수 없습니다.")
            raise ValueError(f"샘플 '{samplename}'을 찾을 수 없습니다.")

        dict_profile = sample_data.fillna("").iloc[0].to_dict()

        # 프로파일 딕셔너리 생성
        dict_profile_set = {}
        for marker in list_markers:
            value = str(dict_profile.get(marker, ""))
            if value:  # 더 pythonic한 빈 문자열 체크
                dict_profile_set[marker] = set(value.split("-"))

        logger.debug(f"STRProfile 생성 완료 (samplename={samplename}, 좌위 수={len(dict_profile_set)})")
        return NFS_SP.STRProfile(id=samplename, profile=dict_profile_set)

    def generate_empty_STRProfile(self, samplename="") -> NFS_SP.STRProfile:
        """
        지정된 키트의 모든 마커에 대해 빈 값을 가진 STR 프로파일 객체를 생성합니다.

        주로 혼합 프로필을 생성할 때 시작 프로파일로 사용됩니다.
        모든 마커 위치에 빈 set()이 할당되어 있어 나중에 데이터를 추가할 수 있습니다.

        Args:
            id (str): 생성할 프로필의 id

        Returns:
            STRProfile: 모든 마커가 빈 set으로 초기화된 STR 프로파일 객체

        """
        # 키트에 해당하는 마커 리스트 조회
        list_markers = self.DICT_MARKERS[self.kit]

        # 모든 마커에 대해 빈 set으로 초기화된 프로파일 딕셔너리 생성
        dict_profile_set = {marker: set() for marker in list_markers}

        return NFS_SP.STRProfile(id=samplename, profile=dict_profile_set)

    def update_profile_with_STRProfile(
        self, samplename: str, profile: NFS_SP.STRProfile
    ) -> None:
        """
        STRProfile 객체의 프로필 데이터를 DataFrame에 업데이트합니다.

        지정된 샘플명에 해당하는 행의 각 로커스 컬럼에 STRProfile의
        알릴 정보를 문자열 형태로 업데이트합니다.

        Args:
            samplename (str): 업데이트할 감정물 번호/샘플 이름
            profile (STRProfile): 업데이트할 프로필 데이터를 담은 STRProfile 객체

        Returns:
            None: 함수는 df_profile을 직접 수정하며 반환값이 없습니다.

        Raises:
            ValueError: 샘플명이 데이터에서 찾을 수 없는 경우

        Examples:
            >>> str_profile = NFS_SP.STRProfile(id="S001", profile={"D3S1358": {"15", "16"}})
            >>> update_profile_with_STRProfile("S001", str_profile)
            # df_profile의 S001 행이 업데이트됨
        """
        # 샘플 존재 여부 확인
        sample_mask = self.df_profile["감정물번호"] == samplename
        if not sample_mask.any():
            raise ValueError(f"샘플 '{samplename}'을 찾을 수 없습니다.")

        # STRProfile 데이터를 문자열로 변환
        profile_data = profile.export_to_str()

        # 각 로커스별 알릴 정보 업데이트
        for locus, allele in profile_data.items():
            self.df_profile.loc[sample_mask, locus] = allele

    def insert_new_profile_with_STRProfile(self, code_case, samplename, profile: NFS_SP.STRProfile):
        # 샘플 존재 여부 확인
        sample_mask = self.df_profile["감정물번호"] == samplename
        if sample_mask.any():
            raise ValueError(f"'{samplename}'은 이미 존재합니다. update_profile_with_STRProfile를 이용하세요.")
        new_row = {
            '접수번호': code_case,
            '감정물번호': samplename,
            'STATUS_COMBINED': 'UNIQUE'
        }
        profile_data = profile.export_to_str()
        for locus, allele in profile_data.items():
            new_row[locus] = allele
        self.df_profile.loc[len(self.df_profile)]= pd.Series(new_row)

    def delete_profile_by_samplename(self, samplename):
        """
        samplename으로 프로필 삭제

        Args:
            samplename: 삭제할 감정물번호

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # df_profiles에서 해당 행 찾기
            indices = self.df_profile[
                self.df_profile["감정물번호"] == samplename
                ].index

            if indices.empty:
                return False  # 프로필이 존재하지 않음

            # 행 삭제
            self.df_profile.drop(indices, inplace=True)
            self.df_profile.reset_index(drop=True, inplace=True)

            return True

        except Exception as e:
            raise Exception(f"프로필 삭제 실패: {str(e)}")

    def check_inclusion(self, target_samplename: str, query_samplename: str) -> bool:
        """
        타겟 샘플이 쿼리 샘플을 포함하는지 확인합니다.

        두 샘플의 STR 프로필을 생성하고, 타겟 프로필이 쿼리 프로필의
        모든 알릴을 포함하는지 검사합니다. (20개 마커 사용)

        Args:
            target_samplename (str): 포함 여부를 확인할 대상 샘플명
            query_samplename (str): 포함되는지 확인할 쿼리 샘플명

        Returns:
            bool: 타겟이 쿼리를 포함하면 True, 그렇지 않으면 False

        Examples:
            >>> analyzer.check_inclusion("mixed_sample", "contributor1")
            True
            >>> analyzer.check_inclusion("single_sample", "different_sample")
            False
        """
        logger.debug(f"포함 확인 시작 (target={target_samplename}, query={query_samplename})")
        # STR 프로필 생성 (20개 마커 사용)
        target_profile = self.generate_STRProfile(target_samplename, STR_20=True)
        query_profile = self.generate_STRProfile(query_samplename, STR_20=True)
        # 포함 관계 확인
        result = target_profile.check_inclusion(query_profile)
        logger.info(f"포함 확인 완료 (target={target_samplename}, query={query_samplename}, result={result})")
        return result

    def check_match(self, target_samplename: str, query_samplename: str) -> bool:
        """
        두 샘플의 STR 프로필이 일치하는지 확인합니다.

        두 샘플의 STR 프로필을 생성하고, 모든 로커스에서
        알릴이 정확히 일치하는지 검사합니다. (20개 마커 사용)

        Args:
            target_samplename (str): 비교할 첫 번째 샘플명
            query_samplename (str): 비교할 두 번째 샘플명

        Returns:
            bool: 두 프로필이 일치하면 True, 그렇지 않으면 False

        Examples:
            >>> analyzer.check_match("sample1", "sample2")
            False
            >>> analyzer.check_match("sample1", "sample1_duplicate")
            True
        """
        logger.debug(f"일치 확인 시작 (target={target_samplename}, query={query_samplename})")
        # STR 프로필 생성 (20개 마커 사용)
        target_profile = self.generate_STRProfile(target_samplename, STR_20=True)
        query_profile = self.generate_STRProfile(query_samplename, STR_20=True)

        # 일치 여부 확인
        result = target_profile.check_match(query_profile)
        logger.info(f"일치 확인 완료 (target={target_samplename}, query={query_samplename}, result={result})")
        return result

    def generate_mix_profile(self, samplenames: list) -> NFS_SP.STRProfile:
        """
        여러 샘플의 STR 프로필을 결합하여 혼합 프로필을 생성합니다.

        빈 STR 프로필로 시작하여 각 샘플의 프로필을 순차적으로
        결합(union)하여 최종 혼합 프로필을 생성합니다.

        Args:
            samplenames (list[str]): 혼합할 샘플명들의 리스트

        Returns:
            STRProfile: 모든 입력 샘플들의 알릴이 결합된 혼합 프로필

        Raises:
            ValueError: samplenames가 비어있는 경우

        Examples:
            >>> mixed = analyzer.generate_mix_profile(["sample1", "sample2", "sample3"])
            >>> print(len(mixed.profile))  # 결합된 프로필의 마커 수
        """
        logger.info(f"혼합 프로필 생성 시작 (샘플 수={len(samplenames)})")
        # 입력 유효성 검사
        if not samplenames:
            logger.error("ValueError: 혼합할 샘플명 리스트가 비어있습니다.")
            raise ValueError("혼합할 샘플명 리스트가 비어있습니다.")

        # 빈 프로필로 시작
        mixed_profile = self.generate_empty_STRProfile()

        # 각 샘플의 프로필을 순차적으로 결합
        for samplename in samplenames:
            logger.debug(f"샘플 병합 중: {samplename}")
            element_profile = self.generate_STRProfile(samplename)
            mixed_profile = mixed_profile.union_profiles(element_profile)

        logger.info(f"혼합 프로필 생성 완료 (샘플 수={len(samplenames)}, 마커 수={len(mixed_profile.profile)})")
        return mixed_profile