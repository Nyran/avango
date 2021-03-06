#basic
import sys
import math

#avango gua
import avango
import avango.script
from avango.script import field_has_changed
import avango.gua
from examples_common.GuaVE import GuaVE

#multiscale
import navigator
import scenes

class DistanceMapWrapper(avango.script.Script):
  DistanceMapNode = avango.gua.SFDepthMapNode()
  MinDistance = avango.SFFloat()
  MinDistancePos = avango.gua.SFVec3()

  def __init__(self):
    self.super(DistanceMapWrapper).__init__()
    self.DistanceMapNode.value = None
    self.always_evaluate(True)

  def evaluate(self):
    self.MinDistance.value = self.DistanceMapNode.value.MinDistance.value
    self.MinDistancePos.value = self.DistanceMapNode.value.MinDistanceWorldPosition.value


class ClippingUpdater(avango.script.Script):
  MinDistance = avango.SFFloat()
  Near = avango.SFFloat()
  Far = avango.SFFloat()

  @field_has_changed(MinDistance)
  def update(self):
    if self.MinDistance.value == -1.0:
      self.Near.value *= 1.5
    else:  
      if self.MinDistance.value < (self.Near.value*3):
        self.Near.value *= 0.6
      if self.MinDistance.value > (self.Near.value*10):
        self.Near.value *= 1.5
    
    self.Near.value = min(self.Near.value, 10)
    self.Near.value = max(self.Near.value, 0.0001)
    self.Far.value = self.Near.value * 1000.0


class MarkerUpdater(avango.script.Script):
  MinDistance = avango.SFFloat()
  MinDistancePos = avango.gua.SFVec3()
  OutTransform = avango.gua.SFMatrix4()
  
  def evaluate(self):
    distance = self.MinDistance.value
    pos = self.MinDistancePos.value

    self.OutTransform.value = avango.gua.make_trans_mat(pos) * avango.gua.make_scale_mat(distance/50)


class ArrowUpdater(avango.script.Script):
  NavigationTransformIn = avango.gua.SFMatrix4()
  NearClip = avango.SFFloat()
  MinDistance = avango.SFFloat()
  MinDistancePos = avango.gua.SFVec3()
  EvasionInfo = avango.SFBool()
  OutTransform = avango.gua.SFMatrix4()
  OutMaterial = avango.gua.SFMaterial()


  def __init__(self):
    self.super(ArrowUpdater).__init__()
    self.MinDistance.value = -1.0
    self.OutTransform.value = avango.gua.make_identity_mat()
    self.OutMaterial.value = avango.gua.nodes.Material()

  @field_has_changed(EvasionInfo)
  def update_color(self):
    if self.EvasionInfo.value:
      self.OutMaterial.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
    else:
      self.OutMaterial.value.set_uniform("Color", avango.gua.Vec4(0.4, 0.9, 0.4, 1.0))

  @field_has_changed(NavigationTransformIn)
  def update_arrow(self):
    scale = self.NearClip.value * 0.3
    offset = avango.gua.Vec3(self.NearClip.value * 0.5, self.NearClip.value * -0.22, self.NearClip.value * -1.5)
    if not self.MinDistance.value == -1.0:
      arrow_pos = (self.NavigationTransformIn.value * avango.gua.make_trans_mat(offset)).get_translate()

      look_mat = avango.gua.make_look_at_mat_inv(arrow_pos, self.MinDistancePos.value, avango.gua.Vec3(0.0, 1.0, 0.0))
      nav_rot_mat = (avango.gua.make_rot_mat(self.NavigationTransformIn.value.get_rotate_scale_corrected()))
      rot_mat = avango.gua.make_rot_mat(look_mat.get_rotate())

      self.OutTransform.value = avango.gua.make_trans_mat(offset) * avango.gua.make_inverse_mat(nav_rot_mat) * rot_mat * avango.gua.make_scale_mat(scale)
    else:
      self.OutTransform.value = avango.gua.make_trans_mat(offset) * avango.gua.make_rot_mat(90.0, 1.0, 0.0, 0.0) * avango.gua.make_scale_mat(scale)


class TransformSmoother(avango.script.Script):
  InTransform = avango.gua.SFMatrix4()
  OutTransform = avango.gua.SFMatrix4()
  Smoothness = avango.SFFloat()

  def __init__(self):
    self.super(TransformSmoother).__init__()
    self.always_evaluate(True)
    self.InTransform.value = avango.gua.make_identity_mat()
    self.OutTransform.value = avango.gua.make_identity_mat()

  def evaluate(self):
    if math.isnan(self.OutTransform.value.get_element(0,0)):
      self.OutTransform.value = avango.gua.make_identity_mat()
    in_translate = self.InTransform.value.get_translate()
    in_rotation = self.InTransform.value.get_rotate_scale_corrected()
    in_scale = self.InTransform.value.get_scale()

    out_translate = self.OutTransform.value.get_translate()
    out_rotation = self.OutTransform.value.get_rotate_scale_corrected()
    out_scale = self.OutTransform.value.get_scale()

    out_translate = out_translate * (1.0 - self.Smoothness.value) + in_translate * self.Smoothness.value
    out_rotation = out_rotation.slerp_to(in_rotation, self.Smoothness.value)
    out_scale = out_scale * (1.0 - self.Smoothness.value) + in_scale * self.Smoothness.value

    self.OutTransform.value = avango.gua.make_trans_mat(out_translate) *\
                              avango.gua.make_rot_mat(out_rotation) *\
                              avango.gua.make_scale_mat(out_scale)


def start(scenename, stereo=False):
    print("loading:", scenename, "Stereo:", stereo) 
    # setup scenegraph
    graph = avango.gua.nodes.SceneGraph(Name="scenegraph")

    scene = avango.gua.nodes.TransformNode(
      Transform=avango.gua.make_identity_mat(),
      Name="scene"
      )

    starting_pos = scenes.load_scene(scenename, scene)

    navigation = avango.gua.nodes.TransformNode(
      Transform=avango.gua.make_trans_mat(starting_pos),
      Name="navigation"
      )

    loader = avango.gua.nodes.TriMeshLoader()
    marker = loader.create_geometry_from_file(
        "marker", "data/objects/sphere.obj", avango.gua.LoaderFlags.NORMALIZE_SCALE
    )
    marker.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 1.0 ,1.0 ,1.0))
    marker.Material.value.set_uniform("Emissivity", 0.3)
    marker.Tags.value = ["markers"]

    arrow = loader.create_geometry_from_file(
       "arrow", "data/objects/arrow.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.NORMALIZE_SCALE | avango.gua.LoaderFlags.NORMALIZE_POSITION
    )
    arrow.Tags.value = ["markers"]
    navigation.Children.value.append(arrow)

    graph.Root.value.Children.value.extend([scene, navigation, marker])

    size = avango.gua.Vec2ui(2560, 1440)

    stereomode = avango.gua.StereoMode.MONO
    if stereo:
      stereomode = avango.gua.StereoMode.ANAGLYPH_RED_CYAN

    window = avango.gua.nodes.GlfwWindow(
      Size = size,
      LeftPosition = avango.gua.Vec2ui(0, 0),
      LeftResolution = size,
      RightPosition = avango.gua.Vec2ui(0, 0),
      RightResolution = size,
      StereoMode = stereomode
    )

    avango.gua.register_window("window", window)

    cam = avango.gua.nodes.CameraNode(
      Name = "cam",
      LeftScreenPath = "/navigation/screen",
      RightScreenPath = "/navigation/screen",
      SceneGraph = "scenegraph",
      Resolution = size,
      EyeDistance = 0.06,
      EnableStereo = stereo,
      OutputWindowName = "window",
      ViewID = 1,
      Transform = avango.gua.make_trans_mat(0.0, 0.0, 0.0),
      # BlackList = ["markers"],
    )
    navigation.Children.value.append(cam)

    res_pass = avango.gua.nodes.ResolvePassDescription()
    res_pass.EnableSSAO.value = False
    res_pass.SSAOIntensity.value = 4.0
    res_pass.SSAOFalloff.value = 10.0
    res_pass.SSAORadius.value = 7.0
    res_pass.EnvironmentLightingColor.value = avango.gua.Color(0.1, 0.1, 0.1)
    res_pass.ToneMappingMode.value = avango.gua.ToneMappingMode.UNCHARTED
    res_pass.Exposure.value = 1.0
    res_pass.BackgroundMode.value = avango.gua.BackgroundMode.CUBEMAP_TEXTURE
    if not stereo:
      res_pass.BackgroundTexture.value = "awesome_skymap"

    anti_aliasing = avango.gua.nodes.SSAAPassDescription()

    pipeline_description = avango.gua.nodes.PipelineDescription(
        Passes=[
            avango.gua.nodes.DepthMapPassDescription(),
            avango.gua.nodes.TriMeshPassDescription(),
            avango.gua.nodes.BBoxPassDescription(),
            avango.gua.nodes.SkyMapPassDescription(
              OutputTextureName="awesome_skymap"
            ),
            avango.gua.nodes.PLODPassDescription(),
            avango.gua.nodes.LightVisibilityPassDescription(),
            res_pass,
            anti_aliasing,
            avango.gua.nodes.TexturedScreenSpaceQuadPassDescription(),
            ])

    cam.PipelineDescription.value = pipeline_description

    screen = avango.gua.nodes.ScreenNode(
        Name="screen",
        Transform=avango.gua.make_trans_mat(0.0, 0.0, -0.45),
        Width=0.444,
        Height=0.25,
        )
    navigation.Children.value.append(screen)

    
    dcm_transform = avango.gua.make_identity_mat()
    if stereo:
      dcm_transform = avango.gua.make_trans_mat(0.0, 0.0, -0.20)

    distance_cube_map = avango.gua.nodes.DepthMapNode(
      Name="navigation_depth_cube_map",
      NearClip=0.0001,
      FarClip=1000.0,
      Transform=dcm_transform,
      Resolution=64,
      ViewID=2,
      BlackList=["markers"],
    )
    navigation.Children.value.append(distance_cube_map)

    distance_cube_map_wrapper = DistanceMapWrapper()
    distance_cube_map_wrapper.DistanceMapNode.value = distance_cube_map

    '''
    # NOT SUPPORTED BY GUACAMOLE RIGHT NOW -> textured_screen_space_quad.frag has to be adapted
    debug_quad = avango.gua.nodes.TexturedScreenSpaceQuadNode(
      Name = "DepthMapDebug",
      Texture = distance_cube_map.TextureName.value,
      Width = int(size.x / 2),
      Height = int(size.x / 12),
      Anchor = avango.gua.Vec2(-1.0, -1.0)
      )
    graph.Root.value.Children.value.append(debug_quad)
    '''
    
    navi = navigator.MulitScaleNavigator(
      EnableEvasion=True,
      EnableAdaptiveMotionSpeed=True,
      RotationSpeed=0.3,
      MaxMotionSpeed=300.0,
      MaxDistance=300.0,
      )
    navi.StartLocation.value = navigation.Transform.value.get_translate()
    navi.OutTransform.connect_from(navigation.Transform)
    navi.MinDistance.connect_from(distance_cube_map_wrapper.MinDistance)
    navi.MinDistancePos.connect_from(distance_cube_map_wrapper.MinDistancePos)

    navigation.Transform.connect_from(navi.OutTransform)

    # MarkerUpdate
    marker_updater = MarkerUpdater()
    marker_updater.MinDistance.connect_from(distance_cube_map_wrapper.MinDistance)
    marker_updater.MinDistancePos.connect_from(distance_cube_map_wrapper.MinDistancePos)
    marker_smoother = TransformSmoother(Smoothness=0.2)
    marker_smoother.InTransform.connect_from(marker_updater.OutTransform)
    marker.Transform.connect_from(marker_smoother.OutTransform)
    
    # ArrowUpdate
    arrow_updater = ArrowUpdater()
    arrow_updater.MinDistance.connect_from(distance_cube_map_wrapper.MinDistance)
    arrow_updater.MinDistancePos.connect_from(distance_cube_map_wrapper.MinDistancePos)
    arrow_updater.NavigationTransformIn.connect_from(navigation.Transform)
    arrow_updater.EvasionInfo.connect_from(navi.EvasionInfo)
    arrow_smoother = TransformSmoother(Smoothness=0.2)
    arrow_smoother.InTransform.connect_from(arrow_updater.OutTransform)
    arrow.Transform.connect_from(arrow_smoother.OutTransform)
    arrow.Material.connect_from(arrow_updater.OutMaterial)

    #Clipping update
    clip_updater = ClippingUpdater(
      Near=0.0001,
      # Far=100.0,
    )
    clip_updater.MinDistance.connect_from(distance_cube_map_wrapper.MinDistance)

    cam.NearClip.connect_from(clip_updater.Near)
    cam.FarClip.connect_from(clip_updater.Far)
    # distance_cube_map.NearClip.connect_from(clip_updater.Near)
    # distance_cube_map.FarClip.connect_from(clip_updater.Far)
    arrow_updater.NearClip.connect_from(clip_updater.Near)

    #setup viewer
    viewer = avango.gua.nodes.Viewer()
    viewer.SceneGraphs.value = [graph]
    viewer.Windows.value = [window]

    # def toogle_adaptive_locomotion():

    guaVE = GuaVE()
    guaVE.start(locals(), globals())

    viewer.run()


if __name__ == '__main__':
  if len(sys.argv) == 2:
    start(sys.argv[1])
  elif len(sys.argv) == 3:
    if sys.argv[2] == "stereo":
      start(sys.argv[1], stereo=  True)
    else:
      start(sys.argv[1])
  else:
    print("please pass a scene name as first argument")
    print("available scenes:")
    print(scenes.get_scene_names())
    print("now loading monkey scene")
    start("monkey")

