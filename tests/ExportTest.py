import inspect
import random
import subprocess
from unittest import TestCase
from sklearn.datasets import load_iris
from sklearn import tree
from sklearn.externals import joblib
from nok.Export import Export


class ExportTest(TestCase):
    # python -m unittest discover -p '*Test.py' -v


    def setUp(self):
        self.tmp_fn = 'Tmp'
        self.iris = load_iris()
        self.n_features = len(self.iris.data[0])
        self.clf = tree.DecisionTreeClassifier(random_state=0)
        self.clf.fit(self.iris.data, self.iris.target)


    def tearDown(self):
        del self.clf


    def test_data_type(self):
        self.assertRaises(ValueError, Export.predict, "")


    def test_random_features(self):
        self._create_java_files()

        preds_from_java = []
        preds_from_py = []

        # Creating random features:
        for features in range(150):
            features = [random.uniform(0., 10.) for f in range(self.n_features)]
            preds_from_java.append(self._make_prediction_in_java(features))
            preds_from_py.append(self._make_prediction_in_py(features))

        self._remove_java_files()
        self.assertEqual(preds_from_py, preds_from_java)


    def test_existing_features(self):
        self._create_java_files()

        preds_from_java = []
        preds_from_py = []

        # Getting existing features:
        for features in self.iris.data:
            preds_from_java.append(self._make_prediction_in_java(features))
            preds_from_py.append(self._make_prediction_in_py(features))

        self._remove_java_files()
        self.assertEqual(preds_from_py, preds_from_java)


    def test_command_execution(self):
        joblib.dump(self.clf, self.tmp_fn + '.pkl')
        subprocess.call(['python', inspect.getfile(Export)[:-1], 'Tmp.pkl', 'Tmp.java'])
        subprocess.call(['javac', self.tmp_fn + '.java'])

        preds_from_java = []
        preds_from_py = []

        # Creating random features:
        for features in range(150):
            features = [random.uniform(0., 10.) for f in range(self.n_features)]
            preds_from_java.append(self._make_prediction_in_java(features))
            preds_from_py.append(self._make_prediction_in_py(features))

        subprocess.call(['rm', self.tmp_fn + '.pkl'])
        subprocess.call(['rm', self.tmp_fn + '.pkl_01.npy'])
        subprocess.call(['rm', self.tmp_fn + '.pkl_02.npy'])
        subprocess.call(['rm', self.tmp_fn + '.pkl_03.npy'])
        subprocess.call(['rm', self.tmp_fn + '.pkl_04.npy'])

        self._remove_java_files()
        self.assertEqual(preds_from_py, preds_from_java)


    def _create_java_files(self):
        # Porting to Java:
        tree_src = Export.predict(self.clf)
        with open(self.tmp_fn + '.java', 'w') as file:
            java_src = ('class {0} {{ \n'
                        '    public static {1} \n'
                        '    public static void main(String[] args) {{ \n'
                        '        if (args.length == {2}) {{ \n'
                        '            float[] atts = new float[args.length]; \n'
                        '            for (int i = 0; i < args.length; i++) {{ \n'
                        '                atts[i] = Float.parseFloat(args[i]); \n'
                        '            }} \n'
                        '            System.out.println({0}.predict(atts)); \n'
                        '        }} \n'
                        '    }} \n'
                        '}}').format(self.tmp_fn, tree_src, self.n_features)
            # print java_src
            file.write(java_src)
        # Compiling Java test class:
        subprocess.call(['javac', self.tmp_fn + '.java'])


    def _remove_java_files(self):
        subprocess.call(['rm', self.tmp_fn + '.class'])
        subprocess.call(['rm', self.tmp_fn + '.java'])


    def _make_prediction_in_py(self, features):
        return int(self.clf.predict([features])[0])


    def _make_prediction_in_java(self, features):
        execution = ['java', self.tmp_fn]
        params = [str(f).strip() for f in features]
        command = execution + params
        return int(subprocess.check_output(command).strip())
