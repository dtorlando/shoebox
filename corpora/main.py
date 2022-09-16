import datetime
import decimal
import os

# stores/retrieves objects as files, convenient so we won't have to re-make objects from csv files every time
# which is computationally expensive
import pickle

# contains all file paths we will be working with to original files and major pickled files
# the main file is acting like it exists in the backend folder, dunno why
#   need to fix that
base_path = '../corpora/'
pickled_files = {'links': base_path + 'links.p',
                 'bases': base_path + 'bases.p',
                 'sentences': base_path + 'sentences.p'}
original_files = {'links': base_path + 'links.csv',
                  'bases': base_path + 'base_sentences.csv',
                  'sentences': base_path + 'raw_sentences.csv'}

# language codes for languages we would probably want to work in, ie english, russian, japanese etc
language_codes = ['eng', 'rus', 'ita', 'tur', 'fra', 'por', 'spa', 'hun', 'jpn', 'fin', 'cmn',
                  'ell', 'vie', 'isl', 'kor', 'deu']
restricted_codes = ['cmn', 'jpn', 'kor']

user_codes = ['dot', 'shubby']


# clears all pickle (.p) files (for wanting re-generation)
def clear_pickles(clear_the_pickles):
    if clear_the_pickles:
        for file_name in os.listdir(base_path):
            file = os.path.join(base_path, file_name)
            try:
                if os.path.isfile(file) and file.endswith('.p'):
                    os.remove(file)
            except IndexError:
                assert True, file + ': error occurred with this file'


# base_links has ~10.7 million keys
def create_bases():
    base_links = {}
    try:
        with open(pickled_files['bases'], 'rb') as f:
            base_links = pickle.load(f)
            print("base pickle successfully loaded")
    except IOError:
        print("base pickle failed to load, being created..")
        with open(original_files['bases'], 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # csv file contains sentence which matches to a base
                # ie This is an example sentence // '0'
                # ie Here is another sentence. // '15343'
                # if the base is '0', the sentence is an original
                # if the base is a string of a number,
                #   that corresponds to the id of the sentence from where it was translated
                a, b = line.split('\t')
                assert a.strip() not in base_links, a + " \nthis sentence already in the links file"
                base_links[a.strip()] = b.strip()
        pickle.dump(base_links, open(pickled_files['bases'], 'wb'))

    assert len(base_links) > 0, 'base_links has a 0 length'
    return base_links


def create_tuple_frequencies():
    for language in language_codes:
        if language not in restricted_codes:
            print('create tuple frequencies for ' + language)
            sentence_links = {}
            while not sentence_links:
                try:
                    with open(base_path + language + '.p', 'rb') as f:
                        sentence_links = pickle.load(f)
                        print(language + " sentence pickle successfully loaded")
                except IOError:
                    print(language + ' sentence pickle failed to load... all sentence pickles being created')
                    create_sentences()

                try:
                    with open(base_path + language + '_freq.p', 'rb') as f:
                        # frequency_l = pickle.load(f)
                        print(language + " frequency pickle successfully loaded")
                except IOError:
                    print(language + ' frequency pickle failed to load...  being created')

                    frequency_count = {}
                    tuple_count = 0
                    sentence_count = 0
                    counter = 0
                    length = len(sentence_links)

                    for sentence in sentence_links.values():
                        counter += 1
                        if counter % 100_000 == 0:
                            print(str(counter) + "/" + str(length))
                        split = sentence.lower().split(' ')
                        # split[0] = remove_punctuation(split[0])
                        for start in range(len(split)):
                            for end in range(start + 1, len(split) + 1):
                                constructed_key = ' '.join(split[start:end])
                                frequency_count.setdefault(constructed_key, 0)
                                frequency_count[constructed_key] = frequency_count[constructed_key] + 1
                                tuple_count += 1
                        sentence_count += 1
                    assert len(frequency_count) > 0, language + ' frequency count length is 0'
                    frequency_count = [frequency_count, tuple_count]
                    assert tuple_count > 0, 'tuple count is 0'
                    print('dumping frequency pickle for ' + language)
                    pickle.dump(frequency_count, open(base_path + language + '_freq.p', 'wb'))


# links has ~9 million keys
def create_links():
    sentence_links = {}
    try:
        with open(pickled_files['links'], 'rb') as f:
            sentence_links = pickle.load(f)
            print("links pickle was successfully loaded")
    except IOError:
        print('links pickle failed to load... being created')
        with open(original_files['links'], 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # this file contains sentence_id to sentence_id links which represent translations
                # one id may map to multiple translations, thus each key maps to a list of keys
                a, b = line.split('\t')
                sentence_links.setdefault(a.strip(), [])
                sentence_links[a.strip()].append(b.strip())
        pickle.dump(sentence_links, open(pickled_files['links'], 'wb'))

    assert len(sentence_links) != 0, 'sentence links has a 0 length'
    return sentence_links


# sentences is a very large map, and thus is broken up into smaller language-specific submaps
# for the 16 chosen languages, the combined key size is ~6.9 million
def create_sentences():
    sentences = {}
    try:
        with open(pickled_files['sentences'], 'rb') as f:
            sentences = pickle.load(f)
            print("sentence pickle was successfully loaded")
    except IOError:
        print("sentence pickle failed to load... being created")
        with open(original_files['sentences'], 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # each line is composed of a unique id, the language, and the actual sentence
                sentence_id, language, sentence = line.split('\t')
                # as there are >400 languages,
                #   we only want to obtain sentences from one of our chosen languages
                # a large map of language-specific maps is created,
                #   with submaps mapping ids to sentences for that language
                if language.strip() in language_codes:
                    sentences.setdefault(language.strip(), {})
                    sentences[language.strip()][sentence_id.strip()] = sentence.strip()

        # an empty sentences.p file is created as a basic check for when needing to re-create all submaps
        pickle.dump({}, open(pickled_files['sentences'], 'wb'))

        for language, language_submap in sentences.items():
            # each language-specific submap (english, russian, etc) is dumped into its own file
            pickle.dump(language_submap, open(base_path + language + '.p', 'wb'))


# returns the pickled sub-map for language specified
def get_sentences_pickle(language):
    assert language in language_codes, 'wrong language code given'

    language_d = None

    try:
        with open(base_path + language + '.p', 'rb') as f:
            language_d = pickle.load(f)
    except IOError:
        assert True, 'no such pickle exists for type ' + language

    return language_d


def get_frequency_pickle(lang):
    assert lang in language_codes, 'wrong language code given'
    assert lang not in restricted_codes, 'restricted code given'

    frequency_l = None

    try:
        with open(base_path + lang + '_freq.p', 'rb') as f:
            frequency_l = pickle.load(f)
    except IOError:
        assert True, 'no such frequency pickle exists for type ' + lang

    return frequency_l


# isolated code for playing with programgit
def sandbox():
    eng_d = get_sentences_pickle('eng')
    eng_f = get_frequency_pickle('eng')
    spa_d = get_sentences_pickle('spa')
    rus_d = get_sentences_pickle('rus')
    deu_d = get_sentences_pickle('deu')
    jpn_d = get_sentences_pickle('jpn')
    isl_d = get_sentences_pickle('isl')
    links = create_links()

    listy = [(k, v) for k, v in eng_f[0].items()]
    listy.sort(key=lambda x: x[1], reverse=False)
    # counter = 1
    # for i, e in enumerate(listy):
    #     if i % counter == 0 and e[1] > 1:
    #         print(i, e)
    #         counter *= 2

    for k, sentence in eng_d.items():
        constructed = []
        for one_tuple in sentence.lower().split(' '):
            # print(one_tuple)
            # print(len(eng_f[0]))
            # print(type(eng_f[0]))
            # print(eng_f[0][one_tuple])
            constructed.append((one_tuple, eng_f[0][one_tuple]))
        constructed.sort(key=lambda x: x[1])
        print('======')
        # print(sentence)
        # print(constructed)
        # print(constructed[0][0])
        print(sentence.lower().replace(constructed[0][0], 'xxxxx', 1))

        for translation_key in links[k]:
            if translation_key in eng_d:
                print(eng_d[translation_key])
            if translation_key in spa_d:
                print(spa_d[translation_key])
            if translation_key in deu_d:
                print(deu_d[translation_key])
            if translation_key in isl_d:
                print(isl_d[translation_key])
            if translation_key in rus_d:
                print(rus_d[translation_key])
            if translation_key in jpn_d:
                print(jpn_d[translation_key])



def main():
    # set to True if you wish to delete all saved pickles (re-generation is time consuming)
    clear_pickles(False)

    bases = create_bases()
    links = create_links()
    create_sentences()
    create_tuple_frequencies()

    sandbox()


# program starting point
main()
